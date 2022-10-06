import copy
import http

from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re
import Levenshtein
import difflib
from jsonschema import validate


from onyx_proj.apps.name_matcher.schemas import NAME_MATCHING_INPUT_SCHEMA, VALID_TOKEN_MATCHING_RESULT


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

@csrf_exempt
def get_similarity_v2(request):
    request_body = json.loads(request.body.decode("utf-8"))
    input_name = request_body.get('input_name')
    primary_names = request_body.get('primary_names')

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



def compare_with_payu():
    import csv
    file = open('/tmp/ACQ_BankData.csv')
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
                # similarity_check = _get_similarity(final_data["name"],final_data["beneficiary_name"])
                # #final_data["creditas_similarity"] = 100 if similarity_check["match"]["case"] == "exact_match" else similarity_check["match"]["similarity"]
                # final_data["creditas_similarity"] = 100 if similarity_check["match"]["case"] == "exact_match" else similarity_check["match"]["similarity_v2"]
                req = {
                    "mode":"unformatted",
                    "input_name":{
                        "fullname": final_data["name"]
                    },
                    "primary_names":[
                        {
                        "fullname": final_data["beneficiary_name"]
                }
                    ]
                }
                resp = compare_names(req)
                final_data["creditas_similarity"] = resp["data"]["match_results"][0]["score"]

                final_data['diff'] = True if abs(final_data["creditas_similarity"] -final_data["payu_similarity"] > 20 ) else False
                final_data["creditas_match"] = resp["data"]["match_results"][0]["matched"]
                final_data["bank_status"] = row[15]

                rows.append(final_data)



        except Exception as e:
            continue

    with open('/tmp/payu.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'beneficiary_name', 'payu_similarity', 'creditas_similarity' , 'diff','creditas_match','bank_status'])
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
    orig_inp_name = copy.deepcopy(input_name)
    primary_names = request_body['primary_names']
    deducted_score = 0
    if(request_body.get("mode","") == "unformatted"):
        if input_name.get('fullname') is not None:
            form_name,score = format_unformatted_name(input_name["fullname"])
            deducted_score+=score
            input_name = form_name


    resp = {
        "success":False,
        "data":{
            "input_name":orig_inp_name,
            "match_results":[]
        }
    }

    for name in primary_names:
        final_score = 100 - deducted_score
        form_name = name
        if (request_body.get("mode", "") == "unformatted"):
            if name.get('fullname') is not None:
                form_name, score = format_unformatted_name(name["fullname"])
                final_score-= score
        match_result,ded_score = find_name_similarity(input_name,form_name)
        resp["data"]["match_results"].append({
            "primary_name":name,
            "matched": match_result,
            "score" : min(100,(max(final_score - ded_score,0)))
        })
    resp["success"] = True

    return HttpResponse(json.dumps(resp),status=http.HTTPStatus.OK,content_type="application/json")


def find_name_similarity(first_name,second_name):
    deducted_score = 0

    # lower case applied
    final_first_name = {k:v.lower() for k,v in first_name.items()}
    final_second_name = {k:v.lower() for k,v in second_name.items()}
    first_name = final_first_name
    second_name = final_second_name

    #whitespace removed
    final_first_name = {k: v.strip() for k, v in first_name.items()}
    final_second_name = {k: v.strip() for k, v in second_name.items()}
    if "".join(list(first_name.values())) != "".join(list(final_first_name.values())) or "".join(
            list(second_name.values())) != "".join(list(final_second_name.values())):
        deducted_score+=4
    first_name = final_first_name
    second_name = final_second_name


    #remove salutations
    exhaustive_salutations = ["Mr", "Mrs", "Dr","Miss","Ms"]
    regex = r'\b(?:' + '|'.join(exhaustive_salutations) + ')\.?\s*'
    final_first_name = {k: re.sub(regex, '', v,flags=re.I) for k, v in first_name.items()}
    final_second_name = {k: re.sub(regex, '', v,flags=re.I)  for k, v in second_name.items()}
    if "".join(list(first_name.values())) != "".join(list(final_first_name.values())) or "".join(
            list(second_name.values())) != "".join(list(final_second_name.values())):
        deducted_score += 7
    first_name = final_first_name
    second_name = final_second_name

    salutations = ["C/O","S/O","D/O"]
    for salutation in salutations:
        final_first_name = {k: re.sub(f'{salutation} [A-Za-z ]+', '', v,flags=re.I) for k, v in final_first_name.items()}
        final_second_name = {k: re.sub(f'{salutation} [A-Za-z ]+', '', v,flags=re.I) for k, v in final_second_name.items()}

    if "".join(list(first_name.values())) != "".join(list(final_first_name.values())) or "".join(
            list(second_name.values())) != "".join(list(final_second_name.values())):
        deducted_score += 15
    first_name = final_first_name
    second_name = final_second_name

    #remove specailchars and numbers
    final_first_name = {k: re.sub('[^A-Za-z ]+', '', v) for k, v in first_name.items()}
    final_second_name = {k: re.sub('[^A-Za-z ]+', '', v) for k, v in second_name.items()}
    if "".join(list(first_name.values())) != "".join(list(final_first_name.values())) or "".join(
            list(second_name.values())) != "".join(list(final_second_name.values())):
        deducted_score += 5
    first_name = final_first_name
    second_name = final_second_name


    first_name_tokens = []
    second_name_tokens = []
    first_name_chars = []
    second_name_chars = []

    for k,v in first_name.items():
        first_name_tokens.extend([token for token in v.split(" ") if token!=""])
        [first_name_chars.extend([char for char in token]) for token in v.split(" ")]
    for k,v in second_name.items():
        second_name_tokens.extend([token for token in v.split(" ") if token!=""])
        [second_name_chars.extend([char for char in token]) for token in v.split(" ")]


    #check if both names have same tokens
    if "".join(sorted(first_name_tokens)) == "".join(sorted(second_name_tokens)):
        return True,deducted_score

    #check if one permutation matches with spaces
    first_name_perm = make_permutations(first_name_tokens,delimeter=" ")
    second_name_perm = make_permutations(second_name_tokens,delimeter=" ")
    matches_found = len(set(first_name_perm).intersection(set(second_name_perm)))
    total_permutations = len(set(first_name_perm).union(second_name_perm))
    deducted_score += 10*((total_permutations-matches_found)/total_permutations)
    if matches_found >= 1:
        return True,deducted_score

    # check if one permutation matches without spaces
    first_name_perm = make_permutations(first_name_tokens, "")
    second_name_perm = make_permutations(second_name_tokens, "")
    matches_found = len(set(first_name_perm).intersection(set(second_name_perm)))
    total_permutations = len(set(first_name_perm).union(second_name_perm))
    deducted_score += 10* ((total_permutations - matches_found) / total_permutations)
    if matches_found >= 1:
        return True, deducted_score


    token_matching_results={
        "fname":compare_tokens(first_name["fname"],second_name["fname"]),
        "mname":compare_tokens(first_name["mname"],second_name["mname"]),
        "lname":compare_tokens(first_name["lname"],second_name["lname"]),
    }

    #handle cases like raj kumar & Rajkumar
    if "".join([first_name["fname"].strip(), first_name["mname"].strip()]).lower() == "".join(
            [second_name["fname"].strip(), second_name["mname"].strip()]).lower():
        token_matching_results["fname"]["s_exact"]= True
        token_matching_results["mname"]["s_exact"]= True
        deducted_score+=10


    for valid_seq in VALID_TOKEN_MATCHING_RESULT:
        if(all(token_matching_results[k][v] for k,v in valid_seq["seq"].items())):
            deducted_score += valid_seq["ded_score"]
            return True,deducted_score

    deducted_score+=10  #because name also didn't matched through algo

    total_score = 0
    count=0
    for fname in first_name_perm:
        for sname in second_name_perm:
            total_score+=find_string_similarity(fname,sname)*100
            count+=1

    first_name_perm = make_permutations(first_name_tokens," ")
    second_name_perm = make_permutations(second_name_tokens," ")
    for fname in first_name_perm:
        for sname in second_name_perm:
            total_score += find_string_similarity(fname, sname) * 100
            count += 1

    deducted_score += (70*(100-(total_score/count)))/100

    return False,deducted_score


def compare_tokens(first_name,second_name):

    resp = {
        "s_exact": False,         # single word exact match
        "s_init": False,          # single word initials match
        "missing": False,         # empty word
        "m_exact":False,          # multiple words with atleast exaclty matching 1 word
        "m_exact_init":False,     # multiple words with atleast exaclty matching 1 word and initials match of another word
        "m_init": False           # multiple words with initials matching of atleast 1 word
    }

    if first_name == "" and second_name == "":
        resp["s_exact"] = True
        return resp

    if first_name == "" or second_name == "":
        resp["missing"] = True
        return resp

    if len(first_name.split(" ")) == 1 and len(second_name.split(" ")) == 1:
        if first_name == second_name:
            resp["s_exact"] = True
            return resp
        if (len(first_name)==1 and str(second_name[0]) == first_name) or \
            (len(second_name)==1 and str(first_name[0]) == second_name):
            resp["s_init"] = True
            return resp
        return resp

    first_name_tokens = first_name.split(" ")
    second_name_tokens = second_name.split(" ")
    if not set(first_name_tokens).isdisjoint(set(second_name_tokens)):
        resp["m_exact"] = True
        return resp

    return resp

def format_unformatted_name(name):
    deducted_score = 0

    final_name = name.strip()
    if final_name != name:
        deducted_score+=2
    name = final_name

    exhaustive_salutations = ["Mr", "Mrs", "Dr", "Miss", "Ms"]
    regex = r'\b(?:' + '|'.join(exhaustive_salutations) + ')\.?\s*'
    final_name = re.sub(regex,'',name)
    if final_name != name:
        deducted_score+=5

    name = final_name

    salutations = ["C/O", "S/O", "D/O"]
    for salutation in salutations:
        final_name = re.sub(f'{salutation} [A-Za-z ]+','',final_name)

    if final_name != name:
        deducted_score+=5

    name_tokens = final_name.split(" ")
    formatted_name = {
        "fname": name_tokens[0],
        "mname": " ".join(name_tokens[1:-1]),
        "lname": "" if len(name_tokens) <=1 else name_tokens[-1]
    }
    return formatted_name,deducted_score


def make_permutations(strings = [],delimeter = ""):
    if len(strings) == 0:
        return []

    if len(strings) == 1:
        return strings

    next_perm = []
    final_results = []
    for string in strings:
        next_perm = copy.deepcopy(strings)
        next_perm.remove(string)
        next_permustations = make_permutations(next_perm,delimeter)
        for perm in next_permustations:
            final_results.append(f"{string}{delimeter}{perm}")
    return list(set(final_results))


def generate_ngrams(chars, chars_to_join):
    output = []
    for i in range(len(chars) - chars_to_join + 1):
        output.append("".join(chars[i:i + chars_to_join]))
    return output