from config.settings import es, DEST_INDEX

from elasticsearch.helpers import bulk  # Import bulk helper
import pandas as pd
import numpy as np

def index_documents(merged_data):
    try:
        # Convert NaN to None to avoid Elasticsearch JSON parsing errors
        merged_data = merged_data.replace({np.nan: None})

        # Prepare bulk indexing actions
        if "tranid" in merged_data.columns:
            actions = [
                {
                    "_index": DEST_INDEX,
                    "_id": row["tranid"],
                    "_source": row.to_dict()
                }
                for _, row in merged_data.iterrows()
            ]
        else:
            actions = [
                {
                    "_index": DEST_INDEX,
                    # "_id": row["tranid"],
                    "_source": row.to_dict()
                }
                for _, row in merged_data.iterrows()
            ]
        # Execute bulk operation
        success, errors = bulk(es, actions, raise_on_error=False, stats_only=False)

        # print(f"[INDEX] Successfully indexed {success} documents to {DEST_INDEX}")
        
        if errors:
            # print(f"[INDEX] {len(errors)} documents failed to index")
            # for err in errors[:5]:  # Log only first 5 errors for debugging
            #     print(f"Failed document: {err}")
            return f"{len(errors)} documents failed to index"
        else:
            return True

    except Exception as e:
        # print(f"[ERROR] Failed to index documents: {e}", exc_info=True)
        return f"Failed to index documents: {e}"
    
    # finally:
    #     print("finish")
