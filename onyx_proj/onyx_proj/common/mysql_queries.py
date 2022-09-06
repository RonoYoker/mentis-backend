JOIN_QUERIES = {
    "base_campaign_statuses_query" : """ 
        UPDATE 
          CED_CampaignSchedulingSegmentDetails cssd 
          join CED_CampaignBuilderCampaign cbc on cssd.CampaignId = cbc.UniqueId 
          join CED_CampaignExecutionProgress cep on cssd.Id = cep.CampaignId 
        SET 
          cbc.Status = '{cbc_status}', 
          cep.Status = '{cep_status}', 
          {value_to_set}
          cep.ErrorMsg = '{error_msg}' 
        WHERE 
          cssd.Id = '{id}'
        """
}