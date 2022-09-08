import http

from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
import Levenshtein
import difflib
from jsonschema import validate


from onyx_proj.apps.name_matcher.schemas import NAME_MATCHING_INPUT_SCHEMA


def process_str_for_similarity_cmp(input_str, normalized=False, ignore_list=[], norm_seperator = ''):
    """ Processes string for similarity comparison , method cleans special characters and extra whitespaces
        if normalized is True and substitutes the characters (which are in ignore_list) with "" in input_str

    Args:
        input_str (str) : input string to be processed
        normalized (bool) : if True ,method removes special characters and extra whitespace from string
        ignore_list (list) : list has some characters which has to be substituted with "" in string

    Returns:
       str : returns processed string

    """
    for ignore_str in ignore_list:
        input_str = re.sub(r'{0}'.format(ignore_str), "", input_str, flags=re.IGNORECASE)

    if normalized is True:
        input_str = input_str.strip().lower()
        #clean special chars and extra whitespace
        input_str = re.sub('\W', norm_seperator, input_str).strip()

    return input_str


def find_string_similarity(first_str, second_str, normalized=False, ignore_list=[], compute_mode='default'):
    """ Calculates matching ratio between two strings

    Args:
        first_str (str) : First String
        second_str (str) : Second String
        normalized (bool) : if True ,method removes special characters and extra whitespace
                            from strings then calculates matching ratio
        ignore_list (list) : list has some characters which has to be substituted with "" in string
        compute_mode (str) : String matching algorithm used

    Returns:
       Float Value : Returns float values (matching ratio) in range [0,1] including 0 and 1

    """
    first_str = process_str_for_similarity_cmp(first_str, normalized=normalized, ignore_list=ignore_list)
    second_str = process_str_for_similarity_cmp(second_str, normalized=normalized, ignore_list=ignore_list)
    # match_ratio = (difflib.SequenceMatcher(None, first_str, second_str).ratio() + jellyfish.jaro_winkler(unicode(first_str), unicode(second_str)))/2.0

    if compute_mode == "simplest":
        match_ratio = Levenshtein.ratio(first_str, second_str)
    elif compute_mode == "seq_match":
        s = difflib.SequenceMatcher(None, first_str, second_str)
        match_ratio = sum(n for i, j, n in s.get_matching_blocks()) / float(len(second_str))
    elif compute_mode == "start_first":
        match_ratio = Levenshtein.jaro_winkler(first_str, second_str)
    else:
        match_ratio = (Levenshtein.ratio(first_str, second_str) +
                       Levenshtein.jaro_winkler(first_str, second_str)) / 2.0
    return match_ratio



def find_banking_name_similarity(first_str, second_str):
    first_str_tokens = first_str.split(" ")
    second_str_tokens = second_str.split(" ")

    # concatenated match
    first_str_processed_tokens = {"single":[],"multi":[]}
    second_str_processed_tokens = {"single":[],"multi":[]}

    for token in first_str_tokens:
        if len(token) == 1:
            first_str_processed_tokens['single'].append(token)
        else:
            first_str_processed_tokens['multi'].append(token)

    for token in second_str_tokens:
        if len(token) == 1:
            second_str_processed_tokens['single'].append(token)
        else:
            second_str_processed_tokens['multi'].append(token)

    if (len(first_str_processed_tokens['single']) > 0 or len(second_str_processed_tokens['single']) > 0) and len(first_str_processed_tokens['multi']) == 1 and len(second_str_processed_tokens['multi']) == 1:


        main_similarity = find_banking_name_similarity(first_str_processed_tokens['multi'][0],second_str_processed_tokens['multi'][0])

        if main_similarity < 95:
            #single tokens appended inside name on any side
            first_str_combinations = ["".join(sorted(first_str_processed_tokens['single']))+"".join(sorted(first_str_processed_tokens['multi'])),"".join(sorted(first_str_processed_tokens['multi']))+"".join(sorted(first_str_processed_tokens['single']))]
            second_str_combinations = ["".join(sorted(second_str_processed_tokens['single']))+"".join(sorted(second_str_processed_tokens['multi'])),"".join(sorted(second_str_processed_tokens['multi']))+"".join(sorted(second_str_processed_tokens['single']))]

            comb_max_similarity = 0
            for comb in first_str_combinations:
                for comb1 in second_str_combinations:
                    if comb == comb1:
                        return round((len(comb1) - len(max(first_str_processed_tokens['single'],second_str_processed_tokens['single'])))/len(comb1)*100,2)

                    bank_similar = find_banking_name_similarity(comb,comb1)
                    if bank_similar > comb_max_similarity:
                        comb_max_similarity = bank_similar



            if abs(main_similarity - comb_max_similarity) < 10 :
                return comb_max_similarity




    # if any([any([True if len(token) == 1 else False for token in first_str_tokens]),any([True if len(token) == 1 else False for token in second_str_tokens])]):
    #     if "".join(sorted(first_str_tokens)) == "".join(sorted(second_str_tokens)):
    #         return round(100)



    # con_match = find_string_similarity(first_str.replace(" ",""),second_str.replace(" ",""))
    #
    # if con_match > final_score:
    #     final_processed["final_score"] = round(con_match*100,2)
    # else:
    #     final_processed["final_score"] = round(final_score*100,2)

    comparison_metric = {}
    for str1 in first_str_tokens:
        comparison_metric[str1] = {}
        for str2 in second_str_tokens:
            comparison_metric[str1][str2] = find_string_similarity(str1,str2)

    final_processed = {}
    secondary_selected = []
    for token in first_str_tokens:
        max_score = 0
        selected_token = ""
        for comp_token,score in comparison_metric[token].items():
            print(comp_token,score)
            if score > max_score:
                max_score = score
                selected_token = comp_token

        secondary_selected.append(selected_token)
        final_processed[token] = {"selected":selected_token,"score":max_score}

    for token in second_str_tokens:
        if token not in secondary_selected:
            final_processed[token] = {"selected":None,"score":0}


    final_score = 0
    for token,token_data in final_processed.items():
        if token_data['score'] > 0.5:
            final_score += (token_data['score'] * (1/len(final_processed)))


    return round(final_score*100,2)




def get_similarity(request):
    input_name = request.GET.get('input_name')
    primary_name = request.GET.get('primary_name')

    if input_name is None or primary_name is None:
        response = {"success": False, "info": "mandatory params missing"}
    else:
        response = _get_similarity(input_name,primary_name)


    formatted_repsonse = {"success":True}
    formatted_repsonse['score'] = 100 if response["match"]["case"] == "exact_match" else response["match"]["similarity_v2"]


    return HttpResponse(json.dumps(formatted_repsonse))


def get_similarity_v2(request):
    input_name = request.GET.get('input_name')
    primary_names = request.GET.get('primary_name')

    resp = {
        "success":False,
        "data":[]
        }

    if input_name is None or primary_names is None:
        response = {"success": False, "info": "mandatory params missing"}
    else:
        for name in primary_names:
            response = _get_similarity(input_name,name)
            score = 100 if response["match"]["case"] == "exact_match" else response["match"]["similarity_v2"]
            resp["data"].append({
                "input_name": input_name,
                "primary_name": name,
                "score": score
            })
    resp["success"] = True


    return HttpResponse(json.dumps(resp))

def _get_similarity(input_name,primary_name):
    process_applied = []
    #check exact match
    if input_name == primary_name:
        return {"success":True,"match":{"status":True,"case":"exact_match","process_applied":process_applied}}


    #whitespace trim
    processed_input_name = input_name.strip()
    processed_primary_name = primary_name.strip()

    processed_input_name = re.sub(r'\s{2,}', ' ', processed_input_name)
    processed_primary_name = re.sub(r'\s{2,}', ' ', processed_primary_name)

    if processed_input_name!=input_name or processed_primary_name!=primary_name:
        process_applied.append("whitespace_trim")

    if input_name == primary_name:
        return {"success": True, "match": {"status": True, "case": "exact_match", "process_applied":process_applied}}

    input_name = processed_input_name
    primary_name = processed_primary_name

    processed_input_name = input_name.lower()
    processed_primary_name = primary_name.lower()

    if processed_input_name!=input_name or processed_primary_name!=primary_name:
        process_applied.append("case_changed")

    if input_name == primary_name:
        return {"success": True, "match": {"status": True, "case": "exact_match", "process_applied":process_applied}}

    input_name = processed_input_name
    primary_name = processed_primary_name

    prefixes = ['mr', 'smr', 'dr','er','ms','master','miss','doctor','engineer']
    regex = r'\b(?:' + '|'.join(prefixes) + ')\.?\s*'

    #remove initials
    processed_input_name = re.sub(regex, '', processed_input_name)
    processed_primary_name = re.sub(regex, '', processed_primary_name)

    if processed_input_name != input_name or processed_primary_name != primary_name:
        process_applied.append("initials_removed")

    if input_name == primary_name:
        return {"success": True, "match": {"status": True, "case": "exact_match", "process_applied": process_applied}}

    # remove dots(.)
    input_name = processed_input_name
    primary_name = processed_primary_name

    processed_input_name = processed_input_name.replace(".","")
    processed_primary_name = processed_primary_name.replace(".","")

    if processed_input_name != input_name or processed_primary_name != primary_name:
        process_applied.append("extra_dots_removed")

    if input_name == primary_name:
        return {"success": True, "match": {"status": True, "case": "exact_match", "process_applied": process_applied}}

    # handle unordered tokens

    input_name = processed_input_name
    primary_name = processed_primary_name

    processed_input_name = " ".join(sorted(processed_input_name.split(" ")))
    processed_primary_name = " ".join(sorted(processed_primary_name.split(" ")))

    if processed_input_name != input_name or processed_primary_name != primary_name:
        process_applied.append("unordered_handling")



    if processed_input_name == processed_primary_name:
        return  {"success": True,
                    "match": {"status": True, "case": "exact_match", "process_applied": process_applied},
                    "data": {
                             "processed_input_name": processed_input_name,
                             "processed_primary_name": processed_primary_name}}


    #find string similarity
    similarity = find_string_similarity(processed_input_name,processed_primary_name)

    return {"success": True, "match": {"status": False, "case": "partial_match",
                                              "similarity":round((similarity*100),2),
                                       "similarity_v2":find_banking_name_similarity(processed_input_name,processed_primary_name),
                                              "process_applied": process_applied},
                                    "data": {
                                             "processed_input_name": processed_input_name,
                                             "processed_primary_name": processed_primary_name}}



def compare_with_payu(request):
    import csv
    file = open('/tmp/ACQ_PaymentInfo.csv')
    csvreader = csv.reader(file)
    rows = []
    for row in csvreader:
        if row[8] is None:
            continue

        try :
            payu_response = json.loads(row[8])
            final_data = {}

            if payu_response.get('data',{}).get('accountExists',"NO") == "YES":
                #final_data = {"beneficiary_name":payu_response['data']['beneficiaryName'],"payu_similarity":payu_response['data']["nameMatch"],"cuid":row[1],"payu_ui":True if payu_response['data']["nameMatch"] > 50 else False}
                final_data = {"beneficiary_name":payu_response['data']['beneficiaryName'],"payu_similarity":payu_response['data']["nameMatch"]}
                payu_request = row[7].split("&")
                input_name = ""
                for token in payu_request:
                    token_split = token.split("=")
                    if token_split[0] == "beneName":
                        input_name = token_split[1]
                        break

                if input_name == "":
                    continue

                final_data["name"] = input_name

                #creditas similarty
                similarity_check = _get_similarity(final_data["name"],final_data["beneficiary_name"])
                #final_data["creditas_similarity"] = 100 if similarity_check["match"]["case"] == "exact_match" else similarity_check["match"]["similarity"]
                final_data["creditas_similarity"] = 100 if similarity_check["match"]["case"] == "exact_match" else similarity_check["match"]["similarity_v2"]
                final_data['diff'] = True if abs(final_data["creditas_similarity"] -final_data["payu_similarity"] > 20 ) else False
                rows.append(final_data)



        except Exception as e:
            continue

    with open('/tmp/payu.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'beneficiary_name', 'payu_similarity', 'creditas_similarity' , 'diff'])
        writer.writeheader()
        writer.writerows(rows)



    return HttpResponse(json.dumps({"data":rows}),content_type="application/json")

@csrf_exempt
def compare_names(request):
    request_body = json.loads(request.body.decode("utf-8"))
    try:
        validate(instance=request_body, schema=NAME_MATCHING_INPUT_SCHEMA)
    except Exception as e:
        response = {"success": False, "err": str(e)}
        return HttpResponse(json.dumps(response, default=str), status=http.HTTPStatus.BAD_REQUEST, content_type="application/json")
    input_name = request_body['input_name']
    primary_names = request_body['primary_names']

    resp = {
        "success":False,
        "data":{
            "input_name":input_name,
            "match_results":[]
        }
    }

    for name in primary_names:
        resp["data"]["match_results"].append({
            "primary_name":name,
            "matched": find_name_similarity(input_name,name)
        })
    resp["success"] = True

    return HttpResponse(json.dumps(resp),status=http.HTTPStatus.OK,content_type="application/json")


def find_name_similarity(first_name,second_name):
    pass