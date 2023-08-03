from compass_metrics.db_dsl import get_uuid_count_query
from compass_metrics.db_dsl import get_pr_closed_uuid_count
from datetime import timedelta
from grimoire_elk.enriched.utils import get_time_diff_days
from grimoirelab_toolkit.datetime import str_to_datetime
from compass_common.math_utils import get_medium


def pr_open_time(client, pr_index, date, repos_list):
    query_pr_opens = get_uuid_count_query("avg", repos_list, "time_to_first_attention_without_bot",
                                                "grimoire_creation_date", size=10000, from_date=date-timedelta(days=90), to_date=date)
    query_pr_opens["query"]["bool"]["must"].append({"match_phrase": {"pull_request": "true"}})
    pr_opens_items = client.search(
        index=pr_index, body=query_pr_opens)['hits']['hits']
    if len(pr_opens_items) == 0:
        return None, None
    pr_open_time_repo = []
    for item in pr_opens_items:
        if 'state' in item['_source']:
            if item['_source']['state'] == 'merged' and item['_source']['merged_at'] and str_to_datetime(item['_source']['merged_at']) < date:
                pr_open_time_repo.append(get_time_diff_days(
                    item['_source']['created_at'], item['_source']['merged_at']))
            if item['_source']['state'] == 'closed' and str_to_datetime(item['_source']['closed_at'] or item['_source']['updated_at']) < date:
                pr_open_time_repo.append(get_time_diff_days(
                    item['_source']['created_at'], item['_source']['closed_at'] or item['_source']['updated_at']))
            else:
                pr_open_time_repo.append(get_time_diff_days(
                    item['_source']['created_at'], str(date)))
    if len(pr_open_time_repo) == 0:
        return None, None
    pr_open_time_repo_avg = float(sum(pr_open_time_repo)/len(pr_open_time_repo))
    pr_open_time_repo_mid = get_medium(pr_open_time_repo)
    
    result = {
        "pr_open_time_repo_avg": pr_open_time_repo_avg,
        "pr_open_time_repo_mid": pr_open_time_repo_mid
    }
    
    return result


def closed_pr_count(client, pr_index, date, repos_list):
    query_pr_closed = get_pr_closed_uuid_count(
        "cardinality", repos_list, "uuid", from_date=(date-timedelta(days=90)), to_date=date)
    pr_closed = client.search(index=pr_index, body=query_pr_closed)[
        'aggregations']["count_of_uuid"]['value']
    
    result = {
        "pr_closed": pr_closed
    }
    
    return result