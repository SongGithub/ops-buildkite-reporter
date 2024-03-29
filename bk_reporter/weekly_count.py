# -*- coding: utf-8 -*-
# from bk_reporter.convert_datetime import get_week_number_of_date
from collections import Counter
from bk_reporter.gql_utils import get_gql_resp
from bk_reporter.convert_datetime import get_week_number_of_date

GQL_QUERY_WEEKLY_COUNT_TEAM = {"query": '''{
                  organization(slug:"myob") {
                    teams(first:500) {
                      edges {
                        node {
                          createdAt
                        }
                      }
                    }
                  }
                }'''}

GQL_QUERY_WEEKLY_COUNT_PIPE = {"query": '''{
                  organization(slug:"myob") {
                    pipelines(first:500) {
                      edges {
                        node {
                          createdAt
                        }
                      }
                    }
                  }
                }'''}


def generate_weekly_stat(list_datetime):
    """
        Input : a list of datetime
        Output: a Counter object of sorted date count for each week
                it can be treated as a dict. counter['32.2017']

                {
                    "1.2017": 1,
                    "2.2017": 2,
                    "3.2017": 5
                }
    """
    list_datetime.sort()
    count = Counter(
        [get_week_number_of_date(date) for date in list_datetime]
        )
    return count


def get_accumulated_weekly_stat(counter_obj):
    """
        Input : counter object
        Output: a dict of accumulated results

        i.e.
        Input :
                {
                    "1.2017": 1,
                    "2.2017": 2,
                    "3.2017": 5
                }

        Output:
                {
                    "1.2017": 1,
                    "2.2017": 3,
                    "3.2017": 8
                }
    """
    result = {}
    previous_count = 0
    for key in counter_obj.keys():
        result[key] = counter_obj[key] + previous_count
        previous_count = result[key]
    return result


def join_count_with_topic(count_dict, topic):
    """
        Input :
            - a dict {num_week, count}
            - topic
        Output:
            - {num_week, topic, count}
        i.e.
        input:
            - {'31.2017': 1, '32.2017': 3, '36.2017': 4}
            - "topic": "pipe_count"
        output:
            [
                {"pipe_count": {"week": '31.2017', count: 1}},
                {"pipe_count": {"week": '32.2017', count: 1}},
                {"pipe_count": {"week": '36.2017', count: 8}}
            ]
    """
    result = []
    for key in count_dict.keys():
        result.append(
            {"week": key, "count": count_dict[key]}
        )
    return {topic: result}


def access_createdAt_date(gql_url, gql_query, token, topic):
    """
        Input : gql_query template
        Outout: a list of datetime string representing "createAt" time
    """
    dryrun = False
    gql_resp = get_gql_resp(gql_url, gql_query, dryrun, token)
    nodes = gql_resp["data"]["organization"][topic]["edges"]
    return [datetime["node"]["createdAt"] for datetime in nodes]


def prepare_data_for_csv(dict_datetime, topic):
    """
        Input : dict_datetime {2017.1: 2, 2017.2: 10}
        Output: [
            {2017.1: 1},
            {2017.2: 10}, ...
        ]
    """
    result = []
    for key in dict_datetime.keys():
        result.append({
            "week": key,
            topic: dict_datetime[key]
        })
    print(result)
    return result


def join_results(source_dict, list_target_dict, topic):
    """
        Input:
            - source_list: recently calculated list[{result_dictionary}]
                {
                    {<week>: <pipe_count>}
                }
            - target_list: previously calculated list[{result_dictionary}]
                [{
                    "week": <str>, (i.e. "34.2017")
                    "pass_build": <datetime>,
                    "fail_build": <datetime>
                }]
            - topic: this will be treated as Key for the new dict
        Output:
            Using "week" as "KEY",
            a joined table of results list[{result_dictionary}]
                [{
                    "week": <str>, (i.e. "34.2017")
                    "pass_build": <datetime>,
                    "fail_build": <datetime>
                    "pipe_count": <int> (weekly)
                    "team_count": <int> (weekly)
                }]
    """
    last_value = 0
    for item in list_target_dict:
        if item["week"] in source_dict:
            item.update({topic: source_dict[item["week"]]})
            last_value = source_dict[item["week"]]
        else:
            item.update({topic: last_value})
    return list_target_dict
