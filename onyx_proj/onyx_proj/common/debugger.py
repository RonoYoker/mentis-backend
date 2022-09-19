#
# import datetime
#
# def get_available_slot_count(start_time, end_time, curr_segments):
#     slot_limit = 500
#     curr_segments_map = {}
#     filled_segment_count = {}
#     for x in curr_segments:
#         curr_segments_map.setdefault((x["start"], x["end"]), 0)
#         curr_segments_map[(x["start"], x["end"])] += x["count"]
#
#     curr_segments = sorted(curr_segments, key=lambda x: (x["end"], x["start"]), reverse=True)
#     ordered_list = [(x["start"], x["end"]) for x in curr_segments]
#
#     max_time = curr_segments[0]["end"]
#     min_time = curr_segments[0]["start"]
#     for segment in curr_segments:
#         max_time = max(max_time, segment["end"])
#         min_time = min(min_time, segment["start"])
#     total_slot_count = int((max_time - min_time) / datetime.timedelta(minutes=30))
#     start_slot_index = int((start_time - min_time) / datetime.timedelta(minutes=30))
#     end_slot_index = int((end_time - min_time) / datetime.timedelta(minutes=30))
#     used_segments = []
#     for slot_index in range(total_slot_count - 1, end_slot_index - 1, -1):
#         slot_start_time = min_time + datetime.timedelta(minutes=30 * slot_index)
#         slot_end_time = min_time + datetime.timedelta(minutes=30 * (slot_index + 1))
#         slot_key_pair = (slot_start_time, slot_end_time)
#         keys_remove = []
#         for key_pair in ordered_list:
#             if key_pair[1] < slot_key_pair[1]:
#                 break
#             used_limit = min(curr_segments_map[key_pair], slot_limit - filled_segment_count.get(slot_key_pair, 0))
#             filled_segment_count.setdefault(slot_key_pair, 0)
#             filled_segment_count[slot_key_pair] += used_limit
#             curr_segments_map[key_pair] -= used_limit
#             if curr_segments_map[key_pair] == 0:
#                 curr_segments_map.pop(key_pair,None)
#                 keys_remove.append(key_pair)
#                 used_segments.append(key_pair)
#             if filled_segment_count[slot_key_pair] == slot_limit:
#                 break
#         for keys in keys_remove:
#             ordered_list.remove(keys)
#
#     curr_segments = sorted(curr_segments, key=lambda x: (x["end"], x["start"]))
#     ordered_list = [(x["start"], x["end"]) for x in curr_segments if (x["start"], x["end"]) not in used_segments]
#     print(filled_segment_count)
#
#     for slot_index in range(0, total_slot_count, 1):
#         slot_start_time = min_time + datetime.timedelta(minutes=30 * (slot_index))
#         slot_end_time = min_time + datetime.timedelta(minutes=30 * (slot_index + 1))
#         slot_key_pair = (slot_start_time, slot_end_time)
#         keys_remove = []
#         for key_pair in ordered_list:
#             if key_pair[0] > slot_key_pair[0]:
#                 break
#             used_limit = min(curr_segments_map[key_pair], slot_limit - filled_segment_count.get(slot_key_pair, 0))
#             filled_segment_count.setdefault(slot_key_pair, 0)
#             filled_segment_count[slot_key_pair] += used_limit
#             curr_segments_map[key_pair] -= used_limit
#             if curr_segments_map[key_pair] == 0:
#                 curr_segments_map.pop(key_pair,None)
#                 keys_remove.append(key_pair)
#                 used_segments.append(key_pair)
#             if filled_segment_count[slot_key_pair] == slot_limit:
#                 break
#         for keys in keys_remove:
#             ordered_list.remove(keys)
#     print(filled_segment_count)
#     return slot_limit - filled_segment_count[(start_time, end_time)]
#
#
# def get_avail_count():
#     start_time = datetime.datetime(2022, 1, 1, 1, 30, 0)
#     end_time = datetime.datetime(2022, 1, 1, 2, 0, 0)
#     cur_segments = [
#         {
#             "start": datetime.datetime(2022, 1, 1, 1, 0, 0),
#             "end": datetime.datetime(2022, 1, 1, 1, 30, 0),
#             "count": 400
#
#         },
#         {
#             "start": datetime.datetime(2022, 1, 1, 1, 0, 0),
#             "end": datetime.datetime(2022, 1, 1, 2, 30, 0),
#             "count": 600
#         },
#         {
#             "start": datetime.datetime(2022, 1, 1, 2, 0, 0),
#             "end": datetime.datetime(2022, 1, 1, 2, 30, 0),
#             "count": 200
#         }
#     ]
#
#     val = get_available_slot_count(start_time, end_time, cur_segments)
#     return val
#
#
#
# from sqlalchemy import create_engine
# engine = create_engine("mysql://root:root@localhost/creditascampaignengine",
#                                      echo=True)
#
# from sqlalchemy.orm import sessionmaker
# Session = sessionmaker()
# Session.configure(bind= engine)
# session = Session()
#
# from sqlalchemy import Column,Integer,String, ForeignKey
# from sqlalchemy.orm import relationship
# from sqlalchemy.ext.automap import automap_base
#
# Base = automap_base()
#
#
# class CED_CampaignBuilderCampaign(Base):
#     __tablename__ = 'CED_CampaignBuilderCampaign'
#
#     id = Column("Id", Integer, primary_key=True)
#     campaign_builder_id = Column("CampaignBuilderId",String,ForeignKey("CED_CampaignBuilder.Id"))
#
#
#
# class CED_CampaignBuilder(Base):
#     __tablename__ = 'CED_CampaignBuilder'
#
#     id = Column("Id", Integer, primary_key=True)
#     name = Column("Name",String)
#     segment_id = Column("SegmentId",String,ForeignKey("CED_Segment.Id"))
#     campaign_builder_campaign_list = relationship(CED_CampaignBuilderCampaign,lazy="joined")
#
#
#
# class CED_Segment(Base):
#     __tablename__ = 'CED_Segment'
#
#     id = Column("Id",Integer,primary_key=True)
#     title = Column("Title",String)
#     project_id = Column("ProjectId",String)
#     campaigns = relationship(CED_CampaignBuilder,lazy="joined")
#
# Base.prepare()
#
#
#
# def temp(idx):
#
#     segment = session.query(CED_Segment).filter(CED_Segment.id == idx)
#     result = [{"seg_id":x.id , "camps": x.campaigns } for x  in segment]
#     print (result)
#
#
import json
import http
import requests
import csv
from onyx_proj.apps.segments.segments_processor.segment_headers_processor import *


# def test_fun():
#     # url2 = "http://onyxuat.hyperiontool.com/segments/header_compatibility_check/"
#     url2 = "http://127.0.0.1:8000/segments/header_compatibility_check/"
#     url = "http://uatdev.hyperiontool.com/hyperioncampaigntooldashboard/campaignbuilder/checksegmentcontentcompatible"
#     list1 = []
#     list2 = []
#
#     with open('/home/siddharth/python/contentid.csv', 'r') as csv_file:
#         csv_reader = csv.reader(csv_file)
#         for x in csv_reader:
#             x = x[0]
#             list2.append(x)
#
#     with open('/home/siddharth/python/segmentid.csv') as csv_file:
#         csv_reader = csv.reader(csv_file)
#         for x in csv_reader:
#             x = x[0]
#             list1.append(x)
#     length = len(list2)
#     n = len(list1)
#     listfinal = []
#
#     for i in range(n):
#         listfinal.append([])
#         listfinal[i].append(list1[i])
#         listfinal[i].append(list2[i])
#
#     final_list = []
#     final_list2 = []
#
#     for i in range(length):
#         segment_id = list1[i]
#         content_id = list2[i]
#         dict1 = {"segmentId": segment_id,
#                  "contentId": content_id,
#                  "contentType": "EMAIL"}
#         response1 = requests.post(url, data=json.dumps(dict1),
#                                   headers={'X-AuthToken': '3081F968-2C1A-43CA-A8A5-0B57AF19DB47',
#                                            'Content-Type': 'application/json'})
#         listfinal[i].append(response1.text)
#         print(response1.text)
#
#         dict2 = {"segment_id": segment_id,
#                  "content_id": content_id,
#                  "template_type": "EMAIL"}
#         response = requests.post(url2, data=json.dumps(dict2),
#                                  headers={'X-AuthToken': 'C7DE7DFF-8DE0-41C1-B72E-5C7805E9C5BF',
#                                           'Content-Type': 'application/json'})
#         listfinal[i].append(response.text)
#         print(response.text)
#         print(i+1)
#
#     with open('/home/siddharth/python/final2.csv', 'w') as csv_file:
#         write = csv.writer(csv_file)
#         write.writerows(listfinal)

# test_fun()
def connection_pooling_test():
    pass




def check_name_similarity():
    test_cases = [
        {
            "first": {
                "fname":"Abhishek",
                "mname":"",
                "lname":"Gupta"
            },
            "second": {
                "fname": "abhishek",
                "mname": "",
                "lname": "gupta"
            }
        },
        {
            "first": {
                "fname": "Abhishek",
                "mname": "",
                "lname": "Gupta"
            },
            "second": {
                "fname": "Mr. Abhishek",
                "mname": "",
                "lname": "Gupta"
            }
        },
        {
            "first": {
                "fname": "gupta",
                "mname": "",
                "lname": "abhishek"
            },
            "second": {
                "fname": "Mr. Abhishek",
                "mname": "",
                "lname": "Gupta"
            }
        },
        {
            "first": {
                "fname": "Abhishek",
                "mname": "",
                "lname": "Gupta"
            },
            "second": {
                "fname": "AbhishekGupta",
                "mname": "",
                "lname": ""
            }
        },
        {
            "first": {
                "fname": "Karthik",
                "mname": "",
                "lname": "S"
            },
            "second": {
                "fname": "karthik",
                "mname": "",
                "lname": "S .(2322223"
            }
        },
        {
            "first": {
                "fname": "Abhishek",
                "mname": "",
                "lname": "Gupta"
            },
            "second": {
                "fname": "Abhishek",
                "mname": "kumar",
                "lname": "Gupta"
            }
        },
        {
            "first": {
                "fname": "Abhishek",
                "mname": "kumar",
                "lname": "Gupta"
            },
            "second": {
                "fname": "Abhishek",
                "mname": "Kumar",
                "lname": "G"
            }
        },
        {
            "first": {
                "fname": "Sooraj",
                "mname": "Kumar",
                "lname": ""
            },
            "second": {
                "fname": "Soorajkumar S/O Shish",
                "mname": "",
                "lname": ""
            }
        },
        {
            "first": {
                "fname": "Ankit",
                "mname": "Kumar",
                "lname": ""
            },
            "second": {
                "fname": "AnkitKumarSoAjitKumar",
                "mname": "",
                "lname": ""
            }
        },
        {
            "first": {
                "fname": "Abhishek",
                "mname": "Kumar",
                "lname": "Gupta"
            },
            "second": {
                "fname": "Abhishek",
                "mname": "kumar varma",
                "lname": "gupta"
            }
        },
        {
            "first": {
                "fname": "Abhishek",
                "mname": "Gupta",
                "lname": "Verma"
            },
            "second": {
                "fname": "Abhishek",
                "mname": "Kumar",
                "lname": "Gupta"
            }
        },
        {
            "first": {
                "fname": "Abhishek",
                "mname": "",
                "lname": "K"
            },
            "second": {
                "fname": "Abhishek",
                "mname": "G",
                "lname": "K"
            }
        },
        {
            "first": {
                "fname": "Abhishek",
                "mname": "",
                "lname": "Kumar"
            },
            "second": {
                "fname": "Abhishek",
                "mname": "",
                "lname": "Gupta"
            }
        },
        {
            "first": {
                "fname": "Abhishek",
                "mname": "",
                "lname": ""
            },
            "second": {
                "fname": "Abhishek",
                "mname": "Kumar",
                "lname": "Gupta"
            }
        },
        {
            "first": {
                "fname": "Abhishek",
                "mname": "G",
                "lname": "K"
            },
            "second": {
                "fname": "Abhishek",
                "mname": "Gupta",
                "lname": "Kumar"
            }
        },
        {
            "first": {
                "fname": "Abhishek",
                "mname": "G",
                "lname": "K"
            },
            "second": {
                "fname": "Abhishek",
                "mname": "Gupta",
                "lname": "Kumar"
            }
        },
        {
            "first": {
                "fname": "Abhishek",
                "mname": "G",
                "lname": "K"
            },
            "second": {
                "fname": "Abhishek",
                "mname": "Gupta",
                "lname": "Kumar"
            }
        },
        {
            "first": {
                "fname": "Raj",
                "mname": "Kumar",
                "lname": "L"
            },
            "second": {
                "fname": "Rajkumar",
                "mname": "",
                "lname": "Lakshamanan"
            }
        }

    ]
    from onyx_proj.apps.name_matcher.views import find_name_similarity

    for tc in test_cases :
        result = find_name_similarity(tc["first"],tc["second"])
        print(f"fname::{' '.join(list(tc['first'].values())) }  sname::{' '.join(list(tc['second'].values()))}  result::{result}")

