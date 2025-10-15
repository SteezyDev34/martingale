# -*- coding: utf-8 -*-
"""
Configuration des classes CSS pour les différentes versions du site.
Ce fichier contient les mappings entre les anciennes et nouvelles classes CSS
utilisées pour l'automatisation des paris.
"""

# Dictionnaire des classes CSS pour les éléments de l'interface
classes = {
    'go_to_new_platform_link':
        {
            'old_site': 'go-to-new-platform',

        },
    'scoreboard':
        {
            'old_site': 'c-scoreboard-score__period',
            'new_site': 'scoreboard-status'
        },
    'end_match_stats':
        {
            'old_site': 'after-game-info__text',
            'new_site': 'game-over-panel-banner'
        },
    'resume_text_content':
        {
            'old_site': 'after-game-info__text',
            'new_site': 'game-over-panel-banner'
        },
    'set_container':
        {
            'old_site': 'c-scoreboard-score__period',
            'new_site': 'ui-game-timer__label'
        },
    'score_container':
        {
            'old_site': 'c-scoreboard-score__ball',
            'new_site': 'scoreboard-scores__score'
        },
    'jeu_container':
        {
            'old_site': 'c-scoreboard-player-score__row',
            'new_site': 'scoreboard-periods-table__col'
        },
    'jeu_cell':
        {
            'old_site': 'c-scoreboard-player-score__cell',
            'new_site': 'scoreboard-periods-table-cell--td'
        },
    'period_select':
        {
            'old_site': 'scoreboard-nav__select',
            'new_site': 'game-toolbar__sub-games-dropdown'
        },
    'multiselect_container_wrapper':
        {
            'old_site': 'multiselect__content-wrapper',
            'new_site': 'multiselect__content-wrapper'
        },
    'multiselect_element':
        {
            'old_site': 'multiselect__element',
            'new_site': 'multiselect__element'
        },
    'search_toolbar':
        {
            'old_site': 'scoreboard-nav-items-search',
            'new_site': 'game-toolbar'
        },
    'ui_search_to_click':
        {
            'old_site': 'scoreboard-nav-items-search__input',
            'new_site': 'ui-search-default__button'
        },
    'search_input':
        {
            'old_site': 'scoreboard-nav-items-search__input',
            'new_site': 'ui-search-default__input'
        },
    'bet_list_container':
        {
            'old_site': 'bet_group',
            'new_site': 'market-grid-canvas__container'
        },
    'coupon_bet_remove':
        {
            'old_site': 'cpn-btn cpn-bet__remove',
            'new_site': 'coupon-bet-remove'

        },
    'coupon_bet_remove_lock':
        {
            'old_site': 'cpn-btn__close',
            'new_site': 'coupon-bet-lock-remove'

        },
    'coef_value':
        {
            'old_site': 'cpn-bet__coef',
            'new_site': 'coupon-result-coef-value'
        },
    'cpn_amount':
        {
            'old_site': 'cpn-value-controls',
            'new_site': 'coupon-amount'
        },
    'cpn_amount_input':
        {
            'old_site': 'cpn-value-controls__input',
            'new_site': 'ui-number-input__field'
        },
    'coupon_buttons':
        {
            'old_site': 'cpn-btns-group__item',
            'new_site': 'coupon-buttons'
        },
    'modal_header':
        {
            'old_site': 'c-coupon-modal__header',
            'new_site': 'ui-coupon-modal-header__title'
        },
    'close_modal_btn':
        {
            'old_site': 'c-coupon-modal__close',
            'new_site': 'coupon-success-modal-controls__item'
        },
    'notification_alert':
        {
            'old_site': 'swal2-error',
            'new_site': 'notification-alert'
        },
    'notification_question':
        {
            'old_site': 'swal2-question',
            'new_site': 'notification-question'
        },
    'popup_content':
        {
            'old_site': 'swal2-content',
            'new_site': 'ui-popup__content'
        },
    'popup_submit':
        {
            'old_site': 'swal2-confirm',
            'new_site': 'popup__submit'
        },
    'popup_cancel':
        {
            'old_site': 'swal2-cancel',
            'new_site': 'ui-popup__cancel'
        },
    'preloader':
        {
            'old_site': 'cpn-preloader',
            'new_site': 'coupon-main-tab__preloader'
        },
    'team_name_container':
        {
            'old_site': 'c-tablo__team',
            'news_site': 'scoreboard-intro__team'
        },
    'team_name_text':
        {
            'old_site': 'c-tablo-container__text',
            'new_site': 'scoreboard-team-name__text'
        },
    'dashboard_champ':
        {
            'old_site': 'dashboard-champ-content',
            'new_site': 'dashboard-champ'
        },
    'dashboard_champ_name':
        {
            'old_site': 'c-events__liga',
            'new_site': 'dashboard-champ-name__caption'
        },
    'dashboard_champ_matchlist':
        {
            'old_site': 'c-events-scoreboard__item',
            'new_site': 'dashboard-game-block'
        },
    'dashboard_champ_match_teams_name':
        {
            'old_site': 'c-events__teams',
            'new_site': 'ui-team-scores__teams'
        },
    'dashboard_champ_match_teams_score':
        {
            'old_site': 'c-events-scoreboard__lines',
            'new_site': 'ui-game-scores'
        },
    'score_ball':
        {
            'old_site': 'c-events-scoreboard__ball',
            'new_site': 'ui-game-scores__item--inning'
        },
    'match_link':
        {

            'old_site': 'c-events__name',
            'new_site': 'dashboard-game-block__link'
        },
    'scoreboard_periods_body_container':
        {
            'old_site': 'c-events__name',
            'new_site': 'dashboard-game-block__link'
        },
    'live_content':
        {
            'old_site': 'live-content',
            'new_site': 'betting-content__main'
        },
    'dashboard_champ_body_games':
        {
            'old_site': 'dashboard-champ-content',
            'new_site': 'dashboard-champ-body__games'
        },
    'dashboard_game_block_row':
        {
            'old_site': 'c-events__item_game',
            'new_site': 'dashboard-game-block__row'
        },
    'team_wrap':
        {
            'old_site': 'c-events__teams',
            'new_site': 'dashboard-game-block__teams'
        },
    'team_name':
        {
            'old_site': 'c-events__team',
            'new_site': 'dashboard-game-team-info'
        },
    'cpn_events_trigger':
        {
            'old_site': 'cpn-events__trigger',
            'new_site': 'cpn-events__trigger'
        },
    'cpn_events_input':
        {
            'old_site': 'cpn-events__input',
            'new_site': 'cpn-events__input'
        },
    'cpn_btn_theme_brand':
        {
            'old_site': 'cpn-btn--theme-brand',
            'new_site': 'cpn-btn--theme-brand'
        }

}
