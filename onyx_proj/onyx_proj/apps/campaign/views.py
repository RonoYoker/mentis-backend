import json
import http
from django.shortcuts import HttpResponse
from django.conf import settings

from onyx_proj.common.constants import Roles
from onyx_proj.common.utils.AES_encryption import AesEncryptDecrypt
from onyx_proj.common.decorators import UserAuth
from onyx_proj.apps.campaign.campaign_processor.test_campaign_processor import fetch_test_campaign_data, \
    fetch_test_campaign_validation_status, fetch_test_campaign_validation_status_local
from onyx_proj.apps.campaign.campaign_processor.campaign_content_processor import fetch_vendor_config_data
from onyx_proj.apps.campaign.campaign_monitoring.campaign_stats_processor import get_filtered_campaign_stats, \
    update_campaign_stats_to_central_db, get_filtered_campaign_stats_v2
from onyx_proj.apps.campaign.campaign_processor.campaign_data_processors import save_or_update_campaign_data, \
    get_filtered_dashboard_tab_data, get_min_max_date_for_scheduler, get_time_range_from_date, \
    get_campaign_data_in_period, validate_campaign, create_campaign_details_in_local_db, \
    get_filtered_recurring_date_time, update_segment_count_and_status_for_campaign, update_campaign_status, filter_list, \
    deactivate_campaign_by_campaign_id, view_campaign_data, approval_action_on_campaign_builder_by_unique_id
from apps.campaign.test_campaign.test_campaign_processor import test_campaign_process
from django.views.decorators.csrf import csrf_exempt


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
@UserAuth.user_authentication()
def initiate_test_campaign(request):
    request_body = json.loads(request.body.decode("utf-8"))
    auth_token = request.headers["X-AuthToken"]
    request_body["auth_token"] = auth_token
    response = test_campaign_process(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    return HttpResponse(json.dumps(response, default=str), status=status_code, content_type="application/json")


@csrf_exempt
@UserAuth.user_authentication()
def create_campaign_details(request):
    decrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).decrypt(request.body.decode("utf-8"))
    request_body = json.loads(decrypted_data)
    response = create_campaign_details_in_local_db(request_body)
    status_code = response.pop("status_code", http.HTTPStatus.BAD_REQUEST)
    encrypted_data = AesEncryptDecrypt(key=settings.CENTRAL_TO_LOCAL_ENCRYPTION_KEY).encrypt(
        json.dumps(response, default=str))
    return HttpResponse(encrypted_data, status=status_code, content_type="application/json")