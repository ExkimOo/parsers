import json
import os

import requests

GET_USER_ID_URL = "https://twitter.com/i/api/graphql/qW5u-DAuXpMEG0zA1F7UGQ/UserByScreenName"
GET_USER_TWEETS_URL = "https://twitter.com/i/api/graphql/mpOyZuYdEfndVeVYdSZ6TQ/UserTweets"

# Константные фичи для запросов
FEATURES_USER = '{"hidden_profile_likes_enabled":true,' \
                '"hidden_profile_subscriptions_enabled":true,' \
                '"rweb_tipjar_consumption_enabled":true,' \
                '"responsive_web_graphql_exclude_directive_enabled":true,' \
                '"verified_phone_label_enabled":false,' \
                '"subscriptions_verification_info_is_identity_verified_enabled":true,' \
                '"subscriptions_verification_info_verified_since_enabled":true,' \
                '"highlights_tweets_tab_ui_enabled":true,' \
                '"responsive_web_twitter_article_notes_tab_enabled":true,' \
                '"creator_subscriptions_tweet_preview_api_enabled":true,' \
                '"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,' \
                '"responsive_web_graphql_timeline_navigation_enabled":true}'
FEATURES_TWEETS = r'{"rweb_tipjar_consumption_enabled":true,' \
                  r'"responsive_web_graphql_exclude_directive_enabled":true,' \
                  r'"verified_phone_label_enabled":false,' \
                  r'"creator_subscriptions_tweet_preview_api_enabled":true,' \
                  r'"responsive_web_graphql_timeline_navigation_enabled":true,' \
                  r'"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,' \
                  r'"communities_web_enable_tweet_community_results_fetch":true,' \
                  r'"c9s_tweet_anatomy_moderator_badge_enabled":true,' \
                  r'"articles_preview_enabled":false,' \
                  r'"tweetypie_unmention_optimization_enabled":true,' \
                  r'"responsive_web_edit_tweet_api_enabled":true,' \
                  r'"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,' \
                  r'"view_counts_everywhere_api_enabled":true,' \
                  r'"longform_notetweets_consumption_enabled":true,' \
                  r'"responsive_web_twitter_article_tweet_consumption_enabled":true,' \
                  r'"tweet_awards_web_tipping_enabled":false,' \
                  r'"creator_subscriptions_quote_tweet_preview_enabled":false,' \
                  r'"freedom_of_speech_not_reach_fetch_enabled":true,' \
                  r'"standardized_nudges_misinfo":true,' \
                  r'"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,' \
                  r'"tweet_with_visibility_results_prefer_gql_media_interstitial_enabled":false,' \
                  r'"rweb_video_timestamps_enabled":true,' \
                  r'"longform_notetweets_rich_text_read_enabled":true,' \
                  r'"longform_notetweets_inline_media_enabled":true,' \
                  r'"responsive_web_enhance_cards_enabled":false}'

# Дефолтные заголовки для всех запросов
DEFAULT_HEADERS = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9,de;q=0.8,ru;q=0.7,fr;q=0.6,zh-CN;q=0.5,zh;q=0.4',
    'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZ'
                     'z4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
    'content-type': 'application/json',
    'dnt': '1',
    'referer': 'https://twitter.com/elonmusk/status/1780370067987009711',
    'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'x-client-transaction-id': 'J3tIpgeTiP6Za69R2uxjwLkXT/lRciLD70Ko9C6Mbo+CsRr+'
                               'DRDRbFZl7y79HABo1rFT9yZ7/GG+HlfBW+PRXihdd4pyJA',
    'x-client-uuid': 'f0d8bb68-921f-4590-b201-fa89a63465c6',
    'x-csrf-token': '77a685e30250b8c9451c052ab68081ec73b2880f0c151c95ac90d76588e26ce65f881ab69e91962dd8a8'
                    'e7ef13990f4e9a902b74b5ea1a09af95bb4ce28af5db68cc78958e2a050ddf3ffd0bbd7bd85c',
    'x-twitter-active-user': 'yes',
    'x-twitter-auth-type': 'OAuth2Session',
    'x-twitter-client-language': 'en',
}

# Куки для авторизации, чтобы суметь спарсить ссылки на комментаторов
COOKIES = {

}

# proxies = {
#     "http": "socks5://24.249.199.12:4145",
#     "https": "socks5://24.249.199.12:4145",
#     "socks5": "socks5://24.249.199.12:4145",
# }


def get_user_id(username: str) -> str:
    """
    Получает id пользователя твиттера по его имени для использования в дальнейших запросах

    :param username: имя пользователя в твиттере
    :return: id пользователя
    """
    params = {
        'variables': f'{{"screen_name":"{username}","withSafetyModeUserFields":true}}',
        'features': FEATURES_USER
    }

    response = requests.get(
        GET_USER_ID_URL,
        params=params,
        cookies=COOKIES,
        headers=DEFAULT_HEADERS,
        # proxies=proxies,
    )

    user_id = response.json()["data"]["user"]["result"]["rest_id"]

    return user_id


def parse_tweets(user_id: str, tweets_number: int) -> list:
    """
    Парсит твиты пользователя и их id

    :param user_id: id пользователя
    :param tweets_number: количество твитов пользователя, которые нужно спарсить
    :return: список словарей вида {"tweet_id": str, "text": str}
    """
    # Курсор. Показывает с какого места динамически подгружать твиты, если требуется больше 1 запроса
    cursor = None
    tweets = []

    while len(tweets) < tweets_number:
        variables = {
            "userId": user_id,
            "count": tweets_number,
            "cursor": cursor,
            "includePromotedContent": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True,
        }

        params = {
            'variables': json.dumps(variables),
            'features': FEATURES_TWEETS,
        }

        response = requests.get(
            GET_USER_TWEETS_URL,
            params=params,
            cookies=COOKIES,
            headers=DEFAULT_HEADERS,
            # proxies=proxies,
        )

        instructions = response.json()["data"]["user"]["result"]["timeline_v2"]["timeline"]["instructions"]
        # Отфильтровываем на нужный нам тип, в котором лежат твиты и курсоры
        entries = list(filter(lambda x: x["type"] == "TimelineAddEntries", instructions))
        entries = entries[0]["entries"] if entries else []

        # Находим твиты
        good_entries = list(filter(lambda x: x["entryId"].startswith("tweet"), entries))

        for entry in good_entries:
            # TweetWithVisibilityResults - ретвиты с ограниченным доступом, реклама
            if entry["content"]["itemContent"]["tweet_results"]["result"]["__typename"] != "TweetWithVisibilityResults":
                text = entry["content"]["itemContent"]["tweet_results"]["result"]["legacy"]["full_text"]
                if not text.startswith("RT @"):
                    text = " ".join(x for x in text.split() if not x.startswith("https://t.co/"))
                    tweet_id = entry["content"]["itemContent"]["tweet_results"]["result"]["legacy"]["id_str"]
                    tweets.append({"tweet_id": tweet_id, "text": text})

        # Забираем курсор, если понадобится для следующего запроса
        cursor = list(filter(lambda x: x["entryId"].startswith("cursor-bottom"), entries))
        cursor = cursor[0]["content"]["value"] if cursor else None

    return tweets[:tweets_number]


def parse_commentators(tweets: list, commentators_number: int) -> list:
    '''
    Парсит ссылки на комментаторов твитов по их id

    :param tweets: список словарей вида {"tweet_id": str, "text": str}
    :param commentators_number: количество комментаторов для парсинга
    :return: список словарей вида {"text": str, "commentators": list, "link": str}
    '''
    # Курсор. Показывает с какого места динамически подгружать комментаторов, если требуется больше 1 запроса
    cursor = None

    # Проходимся по твитам
    for tweet in tweets:
        commentators = []
        # Собираем ссылки на комментаторах, пока не достигнем нужного нам числа
        while len(commentators) < commentators_number:
            variables = {
                "focalTweetId": f"{tweet['tweet_id']}",
                "cursor": cursor,
                "referrer": "profile",
                "controller_data": "DAACDAABDAABCgABAAAAAAAAAAAKAAkOsV9KxtaQAQAAAAA=",
                "with_rux_injections": False,
                "includePromotedContent": True,
                "withCommunity": True,
                "withQuickPromoteEligibilityTweetFields": True,
                "withBirdwatchNotes": True,
                "withVoice": True,
                "withV2Timeline": True
            }

            params = {
                'variables': json.dumps(variables),
                'features': FEATURES_TWEETS,
            }

            response = requests.get(
                'https://twitter.com/i/api/graphql/zJvfJs3gSbrVhC0MKjt_OQ/TweetDetail',
                params=params,
                cookies=COOKIES,
                headers=DEFAULT_HEADERS,
                # proxies=proxies,
            )

            instructions = response.json()["data"]["threaded_conversation_with_injections_v2"]["instructions"]
            entries = list(filter(lambda x: x["type"] == "TimelineAddEntries", instructions))
            entries = entries[0]["entries"] if entries else []
            good_entries = list(filter(lambda x: x["entryId"].startswith("conversationthread"), entries))

            for i in range(len(good_entries)):
                # TweetWithVisibilityResults - твиты-реклама, появляются в рандомных местах от запроса к запросу
                if good_entries[i]["content"]["items"][0]["item"]["itemContent"]["tweet_results"] \
                        ["result"]["__typename"] != "TweetWithVisibilityResults":
                    result = good_entries[i]["content"]["items"][0]["item"]["itemContent"]["tweet_results"]["result"]

                    # Проверка на наличие комментариев
                    if not result:
                        break

                    username = result["core"]["user_results"]["result"]["legacy"]["screen_name"]
                    commentators.append(f"https://twitter.com/{username}")

            if not commentators:
                break

            # Забираем курсор, если понадобится для следующего запроса
            cursor = list(filter(lambda x: x["entryId"].startswith("cursor-bottom"), entries))
            cursor = cursor[0]["content"]["itemContent"]["value"] if cursor else None

        tweet['commentators'] = commentators[:commentators_number]
        tweet['link'] = f"https://twitter.com/elonmusk/status/{tweet.pop('tweet_id')}"

    return tweets


def main():
    username = "elonmusk"
    tweets_number = 10
    commentators_number = 3

    try:
        user_id = get_user_id(username)
        tweets = parse_tweets(user_id, tweets_number)
        commentators = parse_commentators(tweets, commentators_number)

        with open(os.getcwd() + "/output.json", "w", encoding="utf8") as file:
            file.write(json.dumps(commentators, indent=4))

    except Exception as exception:
        print(exception)


if __name__ == "__main__":
    main()
