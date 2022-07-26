
import datetime

def get_available_slot_count(start_time, end_time, curr_segments):
    slot_limit = 500
    curr_segments_map = {}
    filled_segment_count = {}
    for x in curr_segments:
        curr_segments_map.setdefault((x["start"], x["end"]), 0)
        curr_segments_map[(x["start"], x["end"])] += x["count"]

    curr_segments = sorted(curr_segments, key=lambda x: (x["end"], x["start"]), reverse=True)
    ordered_list = [(x["start"], x["end"]) for x in curr_segments]

    max_time = curr_segments[0]["end"]
    min_time = curr_segments[0]["start"]
    for segment in curr_segments:
        max_time = max(max_time, segment["end"])
        min_time = min(min_time, segment["start"])
    total_slot_count = int((max_time - min_time) / datetime.timedelta(minutes=30))
    start_slot_index = int((start_time - min_time) / datetime.timedelta(minutes=30))
    end_slot_index = int((end_time - min_time) / datetime.timedelta(minutes=30))
    used_segments = []
    for slot_index in range(total_slot_count - 1, end_slot_index - 1, -1):
        slot_start_time = min_time + datetime.timedelta(minutes=30 * slot_index)
        slot_end_time = min_time + datetime.timedelta(minutes=30 * (slot_index + 1))
        slot_key_pair = (slot_start_time, slot_end_time)
        keys_remove = []
        for key_pair in ordered_list:
            if key_pair[1] < slot_key_pair[1]:
                break
            used_limit = min(curr_segments_map[key_pair], slot_limit - filled_segment_count.get(slot_key_pair, 0))
            filled_segment_count.setdefault(slot_key_pair, 0)
            filled_segment_count[slot_key_pair] += used_limit
            curr_segments_map[key_pair] -= used_limit
            if curr_segments_map[key_pair] == 0:
                curr_segments_map.pop(key_pair,None)
                keys_remove.append(key_pair)
                used_segments.append(key_pair)
            if filled_segment_count[slot_key_pair] == slot_limit:
                break
        for keys in keys_remove:
            ordered_list.remove(keys)

    curr_segments = sorted(curr_segments, key=lambda x: (x["end"], x["start"]))
    ordered_list = [(x["start"], x["end"]) for x in curr_segments if (x["start"], x["end"]) not in used_segments]
    print(filled_segment_count)

    for slot_index in range(0, total_slot_count, 1):
        slot_start_time = min_time + datetime.timedelta(minutes=30 * (slot_index))
        slot_end_time = min_time + datetime.timedelta(minutes=30 * (slot_index + 1))
        slot_key_pair = (slot_start_time, slot_end_time)
        keys_remove = []
        for key_pair in ordered_list:
            if key_pair[0] > slot_key_pair[0]:
                break
            used_limit = min(curr_segments_map[key_pair], slot_limit - filled_segment_count.get(slot_key_pair, 0))
            filled_segment_count.setdefault(slot_key_pair, 0)
            filled_segment_count[slot_key_pair] += used_limit
            curr_segments_map[key_pair] -= used_limit
            if curr_segments_map[key_pair] == 0:
                curr_segments_map.pop(key_pair,None)
                keys_remove.append(key_pair)
                used_segments.append(key_pair)
            if filled_segment_count[slot_key_pair] == slot_limit:
                break
        for keys in keys_remove:
            ordered_list.remove(keys)
    print(filled_segment_count)
    return slot_limit - filled_segment_count[(start_time, end_time)]


def get_avail_count():
    start_time = datetime.datetime(2022, 1, 1, 1, 30, 0)
    end_time = datetime.datetime(2022, 1, 1, 2, 0, 0)
    cur_segments = [
        {
            "start": datetime.datetime(2022, 1, 1, 1, 0, 0),
            "end": datetime.datetime(2022, 1, 1, 1, 30, 0),
            "count": 400

        },
        {
            "start": datetime.datetime(2022, 1, 1, 1, 0, 0),
            "end": datetime.datetime(2022, 1, 1, 2, 30, 0),
            "count": 600
        },
        {
            "start": datetime.datetime(2022, 1, 1, 2, 0, 0),
            "end": datetime.datetime(2022, 1, 1, 2, 30, 0),
            "count": 200
        }
    ]

    val = get_available_slot_count(start_time, end_time, cur_segments)
    return val



from sqlalchemy import create_engine
engine = create_engine("mysql://root:root@localhost/creditascampaignengine",
                                     echo=True)

from sqlalchemy.orm import sessionmaker
Session = sessionmaker()
Session.configure(bind= engine)
session = Session()

from sqlalchemy import Column,Integer,String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.automap import automap_base

Base = automap_base()


class CED_CampaignBuilderCampaign(Base):
    __tablename__ = 'CED_CampaignBuilderCampaign'

    id = Column("Id", Integer, primary_key=True)
    campaign_builder_id = Column("CampaignBuilderId",String,ForeignKey("CED_CampaignBuilder.Id"))



class CED_CampaignBuilder(Base):
    __tablename__ = 'CED_CampaignBuilder'

    id = Column("Id", Integer, primary_key=True)
    name = Column("Name",String)
    segment_id = Column("SegmentId",String,ForeignKey("CED_Segment.Id"))
    campaign_builder_campaign_list = relationship(CED_CampaignBuilderCampaign,lazy="joined")



class CED_Segment(Base):
    __tablename__ = 'CED_Segment'

    id = Column("Id",Integer,primary_key=True)
    title = Column("Title",String)
    project_id = Column("ProjectId",String)
    campaigns = relationship(CED_CampaignBuilder,lazy="joined")

Base.prepare()



def temp(idx):

    segment = session.query(CED_Segment).filter(CED_Segment.id == idx)
    result = [{"seg_id":x.id , "camps": x.campaigns } for x  in segment]
    print (result)




