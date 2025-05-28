import json

def inject_functions_to_api(app):
    # check if there is a function already defined for this
    if hasattr(app.http._builder, 'get_grok_conversation_by_uid') == False:

        def get_grok_conversation_by_uid(self, uid, cursor=None):
            variables = {'grok_share_id': uid}
            featuers = { 'articles_preview_enabled': True,
            'c9s_tweet_anatomy_moderator_badge_enabled': True,
            'communities_web_enable_tweet_community_results_fetch': True,
            'creator_subscriptions_quote_tweet_preview_enabled': False,
            'creator_subscriptions_tweet_preview_api_enabled': True,
            'freedom_of_speech_not_reach_fetch_enabled': True,
            'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
            'longform_notetweets_consumption_enabled': True,
            'longform_notetweets_inline_media_enabled': True,
            'longform_notetweets_rich_text_read_enabled': True,
            'premium_content_api_read_enabled': False,
            'profile_label_improvements_pcf_label_in_post_enabled': True,
            'responsive_web_edit_tweet_api_enabled': True,
            'responsive_web_enhance_cards_enabled': False,
            'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
            'responsive_web_graphql_timeline_navigation_enabled': True,
            'responsive_web_grok_analysis_button_from_backend': True,
            'responsive_web_grok_analyze_button_fetch_trends_enabled': False,
            'responsive_web_grok_analyze_post_followups_enabled': True,
            'responsive_web_grok_image_annotation_enabled': True,
            'responsive_web_grok_share_attachment_enabled': True,
            'responsive_web_grok_show_grok_translated_post': False,
            'responsive_web_jetfuel_frame': False,
            'responsive_web_twitter_article_tweet_consumption_enabled': True,
            'rweb_tipjar_consumption_enabled': True,
            'standardized_nudges_misinfo': True,
            'tweet_awards_web_tipping_enabled': False,
            'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
            'verified_phone_label_enabled': False,
            'view_counts_everywhere_api_enabled': True}
            if cursor:
                variables["cursor"] = cursor
            params = {'variables':str(json.dumps(variables, separators=(",", ":"))), 
                        'features': str(json.dumps(featuers, separators=(",", ":")))}
            return {'headers': {},'method':"GET", 'url': "https://x.com/i/api/graphql/Ishd84Zga7NEhblatALH6A/GrokShare",'params': params}
        app.http._builder.get_grok_conversation_by_uid =  get_grok_conversation_by_uid

        async def get_grok_conversation_by_uid(self, uid, cursor=None):
            request_data = self._builder.get_grok_conversation_by_uid(self._builder, uid, cursor)
            # convert response_data from tuple to a mapping
            response = await self.__get_response__(**request_data)
            return response
        app.http.get_grok_conversation_by_uid = get_grok_conversation_by_uid
    if hasattr(app.http._builder, 'get_broadcast_by_id') == False:
        # write custom function to get broadcast by id
        def get_broadcast_by_id(self, broadcast_id):
            variables = {'id': broadcast_id}
            features = {
                'articles_preview_enabled': True,
                'c9s_tweet_anatomy_moderator_badge_enabled': True,
                'communities_web_enable_tweet_community_results_fetch': True,
                'creator_subscriptions_quote_tweet_preview_enabled': False,
                'creator_subscriptions_tweet_preview_api_enabled': True,
                'freedom_of_speech_not_reach_fetch_enabled': True,
                'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
                'longform_notetweets_consumption_enabled': True,
                'longform_notetweets_inline_media_enabled': True,
                'longform_notetweets_rich_text_read_enabled': True,
                'premium_content_api_read_enabled': False,
                'profile_label_improvements_pcf_label_in_post_enabled': True,
                'responsive_web_edit_tweet_api_enabled': True,
                'responsive_web_enhance_cards_enabled': False,
                'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
                'responsive_web_graphql_timeline_navigation_enabled': True,
                'responsive_web_grok_analysis_button_from_backend': True,
                'responsive_web_grok_analyze_button_fetch_trends_enabled': False,
                'responsive_web_grok_analyze_post_followups_enabled': True,
                'responsive_web_grok_image_annotation_enabled': True,
                'responsive_web_grok_share_attachment_enabled': True,
                'responsive_web_grok_show_grok_translated_post': False,
                'responsive_web_jetfuel_frame': False,
                'responsive_web_twitter_article_tweet_consumption_enabled': True,
                'rweb_tipjar_consumption_enabled': True,
                'standardized_nudges_misinfo': True,
                'tweet_awards_web_tipping_enabled': False,
                'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
                'verified_phone_label_enabled': False,
                'view_counts_everywhere_api_enabled': True
            }
            params = {
                'variables': json.dumps(variables, separators=(',', ':')),
                'features': json.dumps(features, separators=(',', ':')),
            }
            return {'headers': {},'method':"GET", 'url': "https://x.com/i/api/graphql/TVpOsxrXbB4yWQYxGCjBbw/BroadcastQuery",'params': params}
        app.http._builder.get_broadcast_by_id = get_broadcast_by_id
        async def get_broadcast_by_id(self, broadcast_id):
            response_data = self._builder.get_broadcast_by_id(self._builder, broadcast_id)
            response = await self.__get_response__(**response_data)
            return response
        app.http.get_broadcast_by_id = get_broadcast_by_id
    if hasattr(app.http._builder, 'get_list_subscribers') == False:
        def get_list_subscribers(self, list_id, cursor=None):
            variables = {'listId': list_id, 'count': 20}
            features = { 'articles_preview_enabled': True,
            'c9s_tweet_anatomy_moderator_badge_enabled': True,
            'communities_web_enable_tweet_community_results_fetch': True,
            'creator_subscriptions_quote_tweet_preview_enabled': False,
            'creator_subscriptions_tweet_preview_api_enabled': True,
            'freedom_of_speech_not_reach_fetch_enabled': True,
            'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
            'longform_notetweets_consumption_enabled': True,
            'longform_notetweets_inline_media_enabled': True,
            'longform_notetweets_rich_text_read_enabled': True,
            'premium_content_api_read_enabled': False,
            'profile_label_improvements_pcf_label_in_post_enabled': True,
            'responsive_web_edit_tweet_api_enabled': True,
            'responsive_web_enhance_cards_enabled': False,
            'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
            'responsive_web_graphql_timeline_navigation_enabled': True,
            'responsive_web_grok_analysis_button_from_backend': True,
            'responsive_web_grok_analyze_button_fetch_trends_enabled': False,
            'responsive_web_grok_analyze_post_followups_enabled': True,
            'responsive_web_grok_image_annotation_enabled': True,
            'responsive_web_grok_share_attachment_enabled': True,
            'responsive_web_grok_show_grok_translated_post': False,
            'responsive_web_jetfuel_frame': False,
            'responsive_web_twitter_article_tweet_consumption_enabled': True,
            'rweb_tipjar_consumption_enabled': True,
            'rweb_video_screen_enabled': False,
            'standardized_nudges_misinfo': True,
            'tweet_awards_web_tipping_enabled': False,
            'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
            'verified_phone_label_enabled': False,
            'view_counts_everywhere_api_enabled': True}
            if cursor:
                variables["cursor"] = cursor
            params = {'variables': str(json.dumps(variables, separators=(",", ":"))), 
                        'features': str(json.dumps(features, separators=(",", ":")))}
            return {'headers': {}, 'method': "GET", 'url': "https://x.com/i/api/graphql/R0oek6rVo18vxBqMlXK39Q/ListSubscribers", 'params': params}
        app.http._builder.get_list_subscribers = get_list_subscribers
        async def get_list_subscribers(self, list_id, cursor=None):
            request_data = self._builder.get_list_subscribers(self._builder, list_id, cursor)
            response = await self.__get_response__(**request_data)
            return response
        app.http.get_list_subscribers = get_list_subscribers
    return app