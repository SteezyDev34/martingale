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
            'mobile_site': 'go-to-new-platform'
        },
    'scoreboard':
        {
            'old_site': 'c-scoreboard-score__period',
            'new_site': 'scoreboard-status',
            'mobile_site': 'scoreboard-scores'
        },
    'end_match_stats':
        {
            'old_site': 'after-game-info__text',
            'new_site': 'game-over-panel-banner',
            'mobile_site': 'after-game-info__text'
        },
    'resume_text_content':
        {
            'old_site': 'after-game-info__text',
            'new_site': 'game-over-panel-banner',
            'mobile_site': 'after-game-info__text'
        },
    'set_container':
        {
            'old_site': 'c-scoreboard-score__period',
            'new_site': 'ui-game-timer__label',
            'mobile_site': 'scoreboard-timer'
        },
    'score_container':
        {
            'old_site': 'c-scoreboard-score__ball',
            'new_site': 'scoreboard-scores__score',
            'mobile_site': 'scoreboard-intro__scores'
        },
    'jeu_container':
        {
            'old_site': 'c-scoreboard-player-score__row',
            'new_site': 'scoreboard-periods-table__col',
            'mobile_site': 'scoreboard-periods-column__body'
        },
    'ball_container':
        {
            'old_site': 'c-scoreboard-player-score__row',
            'new_site': 'scoreboard-periods-table__col',
            'mobile_site': 'scoreboard-periods-column__td--has-inning'
        },
    'jeu_cell':
        {
            'old_site': 'c-scoreboard-player-score__cell',
            'new_site': 'scoreboard-periods-table-cell--td',
            'mobile_site': 'scoreboard-periods-column__td'
        },
    'score_ball':
        {
            'old_site': 'c-scoreboard-player-score__ball',
            'new_site': 'scoreboard-periods-table-cell--td',
            'mobile_site': 'scoreboard-periods__inning'
        },
    'score_ball_search':
        {
            'old_site': 'c-scoreboard-player-score__ball',
            'new_site': 'ui-game-scores__item--inning',
            'mobile_site': 'ui-game-scores__item--inning'
        },

    'period_select':
        {
            'old_site': 'scoreboard-nav__select',
            'new_site': 'game-toolbar__sub-games-dropdown',
            'mobile_site': 'scoreboard-nav__select'
        },
    'multiselect_container_wrapper':
        {
            'old_site': 'multiselect__content-wrapper',
            'new_site': 'multiselect__content-wrapper',
            'mobile_site': 'game-sub-games__list'
        },
    'multiselect_element':
        {
            'old_site': 'multiselect__element',
            'new_site': 'multiselect__element',
            'mobile_site': 'game-sub-games__item'
        },
    'search_toolbar':
        {
            'old_site': 'scoreboard-nav-items-search',
            'new_site': 'game-toolbar',
            'mobile_site': 'game-search'
        },
    'ui_search_to_click':
        {
            'old_site': 'scoreboard-nav-items-search__input',
            'new_site': 'ui-search-default__button',
            'mobile_site': 'game-search__input'
        },
    'search_input':
        {
            'old_site': 'scoreboard-nav-items-search__input',
            'new_site': 'ui-search-default__input',
            'mobile_site': 'game-search__input'
        },
    'bet_list_container':
        {
            'old_site': 'bet_group',
            'new_site': 'market-grid-canvas__container',
            'mobile_site': 'game-markets-content'
        },
    'coupon_loader_toggle':
        {
            'old_site': 'coupon-loader-toggle',
            'new_site': 'coupon-loader-toggle',
            'mobile_site': 'coupon-loader-toggle'
        },
    'coupon_loader_input':
        {
            'old_site': 'coupon-loader__input',
            'new_site': 'coupon-loader__input',
            'mobile_site': 'coupon-loader__input'
        },
    'coupon_loader_button':
        {
            'old_site': 'coupon-loader__button',
            'new_site': 'coupon-loader__button',
            'mobile_site': 'coupon-loader__button'
        },
    'coupon_bet_remove':
        {
            'old_site': 'cpn-btn cpn-bet__remove',
            'new_site': 'coupon-bet-remove',
            'mobile_site': 'quick-coupon-events-card__remove'
        },
    'coupon_bet_remove_lock':
        {
            'old_site': 'cpn-btn__close',
            'new_site': 'coupon-bet-lock-remove',
            'mobile_site': 'quick-coupon-events-card-lock__remove'
        },
    'coef_value':
        {
            'old_site': 'cpn-bet__coef',
            'new_site': 'coupon-result-coef-value',
            'mobile_site': 'quick-coupon-events-card-coefs__new'
        },
    'coupon_action_coef':
        {
            'old_site': 'cpn-action-coef',
            'new_site': 'coupon-result-coef-value',
            'mobile_site': 'coupon-total-coef__value'
        },
    'cpn_amount':
        {
            'old_site': 'cpn-value-controls',
            'new_site': 'coupon-amount',
            'mobile_site': 'quick-coupon-bet-amount__steps'
        },
    'cpn_action_amount':
        {
            'old_site': 'cpn-value-controls__action',
            'new_site': 'coupon-amount-action',
            'mobile_site': 'coupon-action-bet__sum'
        },
    'cpn_amount_input':
        {
            'old_site': 'cpn-value-controls__input',
            'new_site': 'ui-number-input__field',
            'mobile_site': 'ui-number-input__field'
        },
    'coupon_buttons':
        {
            'old_site': 'cpn-btns-group__item',
            'new_site': 'coupon-buttons',
            'mobile_site': 'quick-coupon-put-bet-button'
        },
    'modal_header':
        {
            'old_site': 'c-coupon-modal__header',
            'new_site': 'ui-coupon-modal-header__title',
            'mobile_site': 'ui-notification-alert--status-success'
        },
    'close_modal_btn':
        {
            'old_site': 'c-coupon-modal__close',
            'new_site': 'coupon-success-modal-controls__item',
            'mobile_site': 'ui-notification-base__close'
        },
    'notification_alert':
        {
            'old_site': 'swal2-error',
            'new_site': 'notification-alert',
            'mobile_site': 'ui-notification-alert--status-error'
        },
    'notification_question':
        {
            'old_site': 'swal2-question',
            'new_site': 'notification-question',
            'mobile_site': 'ui-notification-alert--status-question'
        },
    'popup_content':
        {
            'old_site': 'swal2-content',
            'new_site': 'ui-popup__content',
            'mobile_site': 'notification-alert__content'
        },
    'popup_submit':
        {
            'old_site': 'swal2-confirm',
            'new_site': 'ui-popup__submit',
            'mobile_site': 'ui-notification-base__close'
        },
    'popup_cancel':
        {
            'old_site': 'swal2-cancel',
            'new_site': 'ui-popup__cancel',
            'mobile_site': 'ui-notification-base__close'
        },
    'preloader':
        {
            'old_site': 'cpn-preloader',
            'new_site': 'coupon-main-tab__preloader',
            'mobile_site': 'ui-button__preloader'
        },
    'team_name_container':
        {
            'old_site': 'c-tablo__team',
            'new_site': 'scoreboard-intro__team',
            'mobile_site': 'scoreboard-intro-team'
        },
    'team_name_text':
        {
            'old_site': 'c-tablo-container__text',
            'new_site': 'scoreboard-team-name__text',
            'mobile_site': 'scoreboard-intro-team__container'
        },
    'dashboard_champ':
        {
            'old_site': 'dashboard-champ-content',
            'new_site': 'dashboard-champ',
            'mobile_site': 'dashboard-champ'
        },
    'dashboard_champ_name':
        {
            'old_site': 'c-events__liga',
            'new_site': 'dashboard-champ-name__label--is-link',
            'mobile_site': 'dashboard-champ-name__label--is-link'
        },
    'dashboard_champ_matchlist':
        {
            'old_site': 'c-events-scoreboard__item',
            'new_site': 'dashboard-game-block',
            'mobile_site': 'dashboard-game-block'
        },
    'dashboard_champ_match_teams_name':
        {
            'old_site': 'c-events__teams',
            'new_site': 'ui-team-scores__teams',
            'mobile_site': 'ui-team-scores__teams'
        },
    'dashboard_champ_match_teams_score':
        {
            'old_site': 'c-events-scoreboard__lines',
            'new_site': 'ui-game-scores',
            'mobile_site': 'ui-game-scores'
        },
    'match_link':
        {
            'old_site': 'c-events__name',
            'new_site': 'dashboard-game-block__link',
            'mobile_site': 'dashboard-game-block__link'
        },
    'scoreboard_periods_body_container':
        {
            'old_site': 'c-events__name',
            'new_site': 'dashboard-game-block__link',
            'mobile_site': 'dashboard-game-block__link'
        },
    'live_content':
        {
            'old_site': 'live-content',
            'new_site': 'betting-content__main',
            'mobile_site': 'betting-content__main'
        },
    'dashboard_champ_body_games':
        {
            'old_site': 'dashboard-champ-content',
            'new_site': 'dashboard-champ-body__games',
            'mobile_site': 'dashboard-champ-body__games'
        },
    'dashboard_game_block_row':
        {
            'old_site': 'c-events__item_game',
            'new_site': 'dashboard-game-block',
            'mobile_site': 'dashboard-game-block'
        },
    'dashboard-game__block':
        {
            'old_site': 'c-events__item_game',
            'new_site': 'dashboard-game__block',
            'mobile_site': 'dashboard-game__block'
        },
    'team_wrap':
        {
            'old_site': 'c-events__teams',
            'new_site': 'dashboard-game-block__teams',
            'mobile_site': 'dashboard-game-block__teams'
        },
    'team_name':
        {
            'old_site': 'c-events__team',
            'new_site': 'dashboard-game-team-info',
            'mobile_site': 'dashboard-game-team-info'
        },
    'cpn_events_trigger':
        {
            'old_site': 'cpn-events__trigger',
            'new_site': 'cpn-events__trigger',
            'mobile_site': 'cpn-events__trigger'
        },
    'cpn_events_input':
        {
            'old_site': 'cpn-events__input',
            'new_site': 'cpn-events__input',
            'mobile_site': 'cpn-events__input'
        },
    'cpn_btn_theme_brand':
        {
            'old_site': 'cpn-btn--theme-brand',
            'new_site': 'cpn-btn--theme-brand',
            'mobile_site': 'cpn-btn--theme-brand'
        },
    'events_time':
        {
            'old_site': 'c-events__time',
            'new_site': 'dashboard-game-block__info',
            'mobile_site': 'dashboard-game-block__info'
        },
    'scoreboard_player_score':
        {
            'old_site': 'c-scoreboard-player-score',
            'new_site': 'scoreboard-player-score',
            'mobile_site': 'scoreboard-periods-column__body'
        },
    'home_navigation_link_search':
        {
            'old_site': 'home-navigation__link--search',
            'new_site': 'games-search-app-search__button',
            'mobile_site': 'home-navigation__link--search'
        },
    'games_search_modal_input':
        {
            'old_site': 'games-search-modal__input',
            'new_site': 'games-search-modal__input',
            'mobile_site': 'games-search-modal__input'
        }
}
