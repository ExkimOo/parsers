import json
import os
import re

import requests

TWITTER_URL = "https://twitter.com/"
GET_BEARER_TOKEN_URL = "https://abs.twimg.com/responsive-web/client-web/main.e46e1035.js"
GET_GUEST_TOKEN_URL = "https://api.twitter.com/1.1/guest/activate.json"
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


def get_tokens(session: requests.Session) -> None:
    """
    Получает bearer и гостевой токен для дальнейших запросов

    :param session: сессия
    :return: None
    """
    # Получаем и сохраняем Bearer токен
    response = session.get(GET_BEARER_TOKEN_URL)
    bearer_token = re.search(r"s=\"([\w\%]{104})\"", response.text)[1]
    session.headers.update({"authorization": f"Bearer {bearer_token}"})

    # Получаем и сохраняем гостевой токен
    guest_token = session.post(GET_GUEST_TOKEN_URL).json()["guest_token"]
    session.headers.update({"x-guest-token": guest_token})


def get_user_id(session: requests.Session, username: str) -> str:
    """
    Получает id пользователя твиттера по его имени для использования в дальнейших запросах

    :param session: сессия
    :param username: имя пользователя в твиттере
    :return: id пользователя
    """
    params = {
        'variables': f'{{"screen_name":"{username}","withSafetyModeUserFields":true}}',
        'features': FEATURES_USER
    }

    response = session.get(
        GET_USER_ID_URL,
        params=params,
    )

    user_id = response.json()["data"]["user"]["result"]["rest_id"]

    return user_id


def parse_tweets(session: requests.Session, user_id: str, tweets_number: int) -> list:
    """
    Парсит твиты пользователя и их id

    :param session: сессия
    :param user_id: id пользователя
    :param tweets_number: количество твитов пользователя, которые нужно спарсить
    :return: список словарей вида {"link": str, "text": str}
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

        response = session.get(
            GET_USER_TWEETS_URL,
            params=params,
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
                    tweets.append({"link": f"https://twitter.com/elonmusk/status/{tweet_id}", "text": text})

        # Забираем курсор, если понадобится для следующего запроса
        cursor = list(filter(lambda x: x["entryId"].startswith("cursor-bottom"), entries))
        cursor = cursor[0]["content"]["value"] if cursor else None

    return tweets[:tweets_number]


def main():
    username = "elonmusk"
    tweets_number = 100

    try:
        session = requests.Session()
        get_tokens(session)
        user_id = get_user_id(session, username)
        tweets = parse_tweets(session, user_id, tweets_number)

        with open(os.getcwd() + "/output.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(tweets, indent=4, ensure_ascii=False))

    except Exception as exception:
        print(exception)


if __name__ == "__main__":
    main()
