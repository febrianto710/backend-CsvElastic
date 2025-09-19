from config.settings import es
from config.settings import DEST_INDEX
from elasticsearch.helpers import bulk  # Import bulk helper
import pandas as pd
import numpy as np

def index_documents(merged_data, index_name):
    try:
        merged_data = merged_data.replace({np.nan: None})
        merged_data.rename(columns=lambda x: "@timestamp" if x.lower() == "@timestamp" else x, inplace=True)

        if index_name == DEST_INDEX["employee"]:
 
            actions = [
                {
                    "_index": index_name,
                    "_id": row["NPP"],
                    "_source": row.to_dict()
                }
                for _, row in merged_data.iterrows()
            ]
        elif index_name == DEST_INDEX["web_portal"]:

            actions = [
                {
                    "_index": index_name,
                    "_id": row["TRX_ID"],
                    "_source": row.to_dict()
                }
                for _, row in merged_data.iterrows()
            ]
        elif index_name == DEST_INDEX["quota_dukcapil"]:

            actions = [
                {
                    "_index": index_name,
                    "_id": row["TRX_ID"],
                    "_source": row.to_dict()
                }
                for _, row in merged_data.iterrows()
            ]
        else: 
            return "Pilihan Tidak Tersedia"
        # Execute bulk operation
        success, errors = bulk(es, actions, raise_on_error=False, stats_only=False)

        # print(f"[INDEX] Successfully indexed {success} documents to {DEST_INDEX}")
        
        if errors:
            return f"{len(errors)} documents failed to index"
        else:
            return True

    except Exception as e:
        # print(f"[ERROR] Failed to index documents: {e}", exc_info=True)
        return f"Failed to index documents: {e}"
    
    # finally:
    #     print("finish")
