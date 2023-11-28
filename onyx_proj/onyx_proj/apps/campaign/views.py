import json
import http
from django.shortcuts import HttpResponse
from django.conf import settings

from onyx_proj.common.constants import Roles
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.common.decorators import UserAuth
from onyx_proj.apps.campaign.campaign_processor.test_campaign_processor import fetch_test_campaign_data, \
    fetch_test_campaign_validation_status, fetch_test_campaign_validation_status_local
from onyx_proj.apps.campaign.campaign_processor.campaign_content_processor import fetch_vendor_config_data, \
    update_campaign_segment_data
from onyx_proj.apps.campaign.campaign_monitoring.campaign_stats_processor import get_filtered_campaign_stats, \
    update_campaign_stats_to_central_db, get_filtered_campaign_stats_v2, get_filtered_campaign_stats_variants
from onyx_proj.common.utils.telegram_utility import TelegramUtility
from onyx_proj.common.decorators import *
from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import save_or_update_campaign_data, \
    get_filtered_dashboard_tab_data, get_min_max_date_for_scheduler, get_time_range_from_date, \
    get_campaign_data_in_period, validate_campaign, create_campaign_details_in_local_db, \
    get_filtered_recurring_date_time, update_segment_count_and_status_for_campaign, update_campaign_status, filter_list, \
    deactivate_campaign_by_campaign_id, view_campaign_data, save_campaign_details, \
    approval_action_on_campaign_builder_by_unique_id, get_camps_detail_between_time, get_camps_detail, \
    update_campaign_by_campaign_builder_ids_local, update_campaign_scheduling_time_in_campaign_creation_details, \
    change_approved_campaign_time, replay_campaign_in_error, check_camp_status,prepare_campaign_builder_campaign
from onyx_proj.apps.campaign.test_campaign.test_campaign_processor import test_campaign_process
from django.views.decorators.csrf import csrf_exempt
from onyx_proj.apps.campaign.system_validation.system_validation_processor import get_campaign_system_validation_status, process_system_validation_entry
from onyx_proj.celery_app.tasks import trigger_eng_data, trigger_campaign_system_validation
from onyx_proj.apps.campaign.campaign_processor.campaign_content_processor import process_favourite
from onyx_proj.models.CED_UserSession_model import CEDUserSession
from onyx_proj.models.CED_User_model import CEDUser
from onyx_proj.models.CED_CampaignBuilder import CEDCampaignBuilder

@csrf_exempt
@UserAuth.user_authentication()
def get_test_campaign_data(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = fetch_test_campaign_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def save_campaign_data(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # process and save campaign data
    response = save_or_update_campaign_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def get_min_max_date(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # process and save campaign data
    response = get_min_max_date_for_scheduler(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def get_time_range_for_date(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # process and save campaign data
    response = get_time_range_from_date(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def get_vendor_config_data(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = fetch_vendor_config_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def get_campaign_data_for_period(request):
    start_date_time = request.GET.get('start_date_time')
    end_date_time = request.GET.get('end_date_time')
    project_id = request.GET.get('project_id')
    content_type = request.GET.get('content_type')

    if start_date_time is None or end_date_time is None or project_id is None or content_type is None:
        return HttpResponse(json.dumps({"success": False, "info": "mandatory params missing"}, default=str),
                            content_type="application/json")

    data = get_campaign_data_in_period(project_id, content_type, start_date_time, end_date_time)
    final_processed_data = []
    for campaign in data:

        if campaign.get('cssd_status', "") == 'COMPLETED':
            campaign['final_processed_status'] = 'COMPLETED'

        if campaign.get('campaign_builder_status', 'SAVED') == 'SAVED':
            campaign['final_processed_status'] = 'CAMPAIGN_NOT_INITIALISED'

        if campaign['campaign_type'] == 'SCHEDULED' and campaign.get('campaign_builder_status',
                                                                     'SAVED') == 'APPROVED' and campaign.get(
                'campaign_id') is None:
            campaign['final_processed_status'] = 'APPROVED_NOT_SCHEDULED'

        if campaign['campaign_type'] == 'SCHEDULED' and campaign.get('cssd_status', "") == 'ERROR':
            campaign['final_processed_status'] = 'ISSUE_IN_SCHEDULER'

        if campaign['campaign_type'] == 'SCHEDULED' and campaign.get('cssd_status', "") == 'SUCCESS':
            campaign['final_processed_status'] = 'SCHEDULED'

        if campaign['campaign_type'] == 'SIMPLE' and campaign.get('campaign_id') is None:
            campaign['final_processed_status'] = 'ISSUE_IN_SCHEDULER'

        if campaign['campaign_type'] == 'SIMPLE' and campaign.get('cssd_status', "") != 'COMPLETED':
            if campaign.get('cssd_status', "") == "LAMBAD_TRIGGERED":
                campaign['final_processed_status'] = 'SCHEDULED'

        final_processed_data.append(campaign)

    return HttpResponse(json.dumps({"success": True, "data": data}, default=str), content_type="application/json")


@csrf_exempt
def generate_recurring_schedule(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    response = get_filtered_recurring_date_time(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    data = response.pop("data", [])
    return HttpResponse(json.dumps({"success": True, "data": data}, default=str), status=status_code,
                        content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def validate_test_campaign(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = validate_campaign(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def update_campaign_progress_status(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # process and save campaign status
    response = update_segment_count_and_status_for_campaign(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def get_campaign_monitoring_stats(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = get_filtered_campaign_stats(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def get_campaign_monitoring_stats_v2(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = get_filtered_campaign_stats_variants(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def update_campaign_stats(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = update_campaign_stats_to_central_db(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def get_dashboard_tab_campaign_data(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # fetch campaign data for dashboard tab
    response = get_filtered_dashboard_tab_data(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def update_camp_status_in_camps_tables(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # update campaign status in campaigns tables
    response = update_campaign_status(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def fetch_campaign_list(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    session_id = request_headers.get('X-Authtoken', '')
    data = filter_list(request_body, session_id)
    status_code = data.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def get_campaign_monitoring_stats_for_admins(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    session_id = request_headers.get('X-Authtoken', '')
    data = dict(body=request_body, headers=session_id)
    # query processor call
    response = get_filtered_campaign_stats_v2(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def test_campaign_validation_status_local(request):
    decrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).decrypt(request.body.decode("utf-8"))
    request_body = json.loads(decrypted_data)
    data = dict(body=request_body, headers=None)
    # query processor call
    response = fetch_test_campaign_validation_status_local(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    encrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).encrypt(
        json.dumps(response, default=str))
    return HttpResponse(encrypted_data, status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def test_campaign_validator(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    session_id = request_headers.get('X-Authtoken', '')
    data = dict(body=request_body, headers=session_id)
    # query processor call
    response = fetch_test_campaign_validation_status(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def save_campaign(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body)
    # process and save campaign data
    response = save_campaign_details(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def deactivate_campaign(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = deactivate_campaign_by_campaign_id(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def get_campaign_data_by_unique_id(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = view_campaign_data(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
@UserAuth.user_validation(permissions=[Roles.APPROVER.value], identifier_conf={
    "param_type": "arg",
    "param_key": 0,
    "param_instance_type": "request_post",
    "param_path": "unique_id",
    "entity_type": "CAMPAIGNBUILDER"
})
def approval_action_on_campaign_builder(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    session_id = request_headers.get('X-Authtoken', '')
    data = dict(body=request_body, headers=session_id)
    response = approval_action_on_campaign_builder_by_unique_id(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def trigger_camp_eng_data(request):
    trigger_eng_data.apply_async(queue="celery_query_executor")
    return HttpResponse("", status=200, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def initiate_test_campaign(request):
    request_body = json.loads(request.body.decode("utf-8"))
    auth_token = request.headers["X-AuthToken"]
    request_body["auth_token"] = auth_token
    response = test_campaign_process(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def create_campaign_details(request):
    decrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).decrypt(request.body.decode("utf-8"))
    request_body = json.loads(decrypted_data)
    response = create_campaign_details_in_local_db(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    encrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).encrypt(
        json.dumps(response, default=str))
    return HttpResponse(encrypted_data, status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def get_campaigns_detail_between_time(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = get_camps_detail_between_time(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def get_campaigns_detail(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = get_camps_detail(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def update_campaign_query_execution_callback_data(request):
    request_body = json.loads(request.body.decode("utf-8"))
    data = update_campaign_segment_data(request_body)
    status_code = data.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")


@csrf_exempt
def deactivate_campaign_by_campaign_builder_ids_local(request):
    request_body = json.loads(AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).decrypt(
        request.body.decode("utf-8")))
    data = dict(body=request_body, headers=None)
    # process and save campaign status
    response = update_campaign_by_campaign_builder_ids_local(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    encrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).encrypt(
        json.dumps(response, default=str))
    return HttpResponse(encrypted_data, status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def get_process_favourite(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    data = dict(body=request_body, headers=request_headers)
    # query processor call
    response = process_favourite(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def update_approved_camp_scheduling_time(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    body = dict(body=request_body, headers=request_headers)
    result = change_approved_campaign_time(body)
    status_code = result.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(result, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def replay_error_campaign(request):
    request_body = json.loads(request.body.decode("utf-8"))
    request_headers = request.headers
    body = dict(body=request_body, headers=request_headers)
    result = replay_campaign_in_error(body)
    status_code = result.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(result, default=str), status=status_code, content_type="application/json")

@csrf_exempt
def update_camp_scheduling_time_in_campaign_creation_details(request):
    request_body = json.loads(AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).decrypt(
        request.body.decode("utf-8")))
    data = dict(body=request_body, headers=None)
    response = update_campaign_scheduling_time_in_campaign_creation_details(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    encrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).encrypt(
        json.dumps(response, default=str))
    return HttpResponse(encrypted_data, status=status_code, content_type="application/json")

@csrf_exempt
def check_campaign_status(request):
    request_body = json.loads(AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).decrypt(
        request.body.decode("utf-8")))
    data = dict(body=request_body, headers=None)
    response = check_camp_status(data)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    encrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).encrypt(
        json.dumps(response, default=str))
    return HttpResponse(encrypted_data, status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def generate_campaign_builder_campaign(request):
    request_body = json.loads(request.body.decode("utf-8"))
    response = prepare_campaign_builder_campaign(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")



@csrf_exempt
@UserAuth.user_authentication()
def trigger_system_validation(request):
    request_body = json.loads(request.body.decode("utf-8"))
    status_code = http.HTTPStatus.BAD_REQUEST
    request_headers = request.headers
    auth_token = request_headers.get('X-Authtoken', '')
    campaign_builder_id = request_body.get("campaign_builder_id", None)
    force = request_body.get("force", False)
    data = {}

    if campaign_builder_id is None:
        return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")

    cb_dict = CEDCampaignBuilder().fetch_campaign_builder_by_unique_id(unique_id=campaign_builder_id)

    user = CEDUserSession().get_user_personal_data_by_session_id(auth_token)

    if request_body.get("test_campaign_mode", "manual") == "system":
        user = CEDUser().get_user_personal_data_by_user_name(cb_dict["CreatedBy"])

    if user is None or len(user) == 0:
        logger.error(f'Unable to fetch user to trigger system Validation On.')
        try:
            alerting_text = f'Unable to trigger system validation due to user not available for request: {request_body}'
            alert_resp = TelegramUtility().process_telegram_alert(project_id=cb_dict.get("ProjectId", ""),
                                                                  message_text=alerting_text,
                                                                  feature_section=settings.HYPERION_ALERT_FEATURE_SECTION.get(
                                                                      "SYSTEM_VALIDATION", "DEFAULT"))
            logger.info(f'Telegram Alert Triggered Response : {alert_resp}, method_name : trigger_system_validation')
        except Exception as ex:
            logger.error(f'Unable to process telegram alerting, method_name: trigger_system_validation, Exp : {ex}')

    user_dict = dict(first_name=user[0].get("FirstName", None), mobile_number=user[0].get("MobileNumber", None),
                     email=user[0].get("EmailId", None))

    """
    Create entry for system validation in respective table in Pushed state.
    IF entry already found, then return error msg in response accordingly.
    """

    if request_body.get("mode", "campaign") == "campaign":
        data = process_system_validation_entry(campaign_builder_id=campaign_builder_id, force=force, user_dict = user_dict)
        if data.get("success", False) is False:
            return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")
        status_code = http.HTTPStatus.OK
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")

@csrf_exempt
@UserAuth.user_authentication()
def get_validation_status(request):
    request_body = json.loads(request.body.decode("utf-8"))
    status_code = http.HTTPStatus.BAD_REQUEST
    data = {}
    campaign_builder_id = request_body.get("campaign_builder_id", None)
    if campaign_builder_id is None:
        data.update({"success": False, "error": "Invalid Input campaign_builder_id"})
        return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")

    if request_body.get("mode", "campaign") == "campaign":
        data = get_campaign_system_validation_status(campaign_builder_id=campaign_builder_id)

    status_code = http.HTTPStatus.OK
    return HttpResponse(json.dumps(data, default=str), status=status_code, content_type="application/json")
