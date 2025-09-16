from config.settings import es, DEST_INDEX, SCROLL_TIME, BATCH_SIZE

from datetime import datetime, timedelta, timezone


# SELECT_FIELDS = ["transaction_date_minute", "avg_max_response_time", "avg_response_time", "avg_tps", "bisnis_value", "max_tps", "success_value", "teknis_value", "total_amount", "total_transaction", "transaction_type", "id"]



def fetch_documents(query, source_index):
    """Fetch documents using the Scroll API."""
    try:
        response = es.search(index=source_index, body=query, scroll=SCROLL_TIME, size=BATCH_SIZE)
        scroll_id = response.get("_scroll_id")
        total_record = response["hits"]["total"]["value"]  # Total number of records

        # print(response)
        if not scroll_id:
            print("No scroll_id received. Exiting...")
            return

        fetched_count = 0  # Track number of documents fetched

        while response["hits"]["hits"]:
            result = response["hits"]["hits"]
            total_doc = len(result)
            fetched_count += total_doc  # Increase count of fetched documents

            remaining = max(0, total_record - fetched_count)  # Ensure it doesn't go negative
            # print(f"Fetched {total_doc} documents (Remaining: {remaining})")
            
            yield result  # Return current batch
            
            response = es.scroll(scroll_id=scroll_id, scroll=SCROLL_TIME)
            scroll_id = response.get("_scroll_id")

            if not scroll_id:
                print("Scroll ID not found in response. Exiting...")
                break

    except Exception as e:
        print("error------------------")
        print(e)
        print("Error fetching documents", exc_info=True)

    finally:
        if scroll_id:
            es.clear_scroll(scroll_id=scroll_id)
            print("Cleared scroll ID.")


