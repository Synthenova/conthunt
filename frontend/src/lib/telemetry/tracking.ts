/**
 * Centralized PostHog tracking utilities
 * Common tracking functions for all user interactions
 */

import { capturePostHog } from "./posthog";

// ============================================
// SEARCH & DISCOVERY TRACKING
// ============================================

export function trackSearchQuerySubmitted(
    query: string,
    platformCount: number,
    platforms: string[],
    deepSearchEnabled: boolean
): void {
    capturePostHog("search_query_submitted", {
        query_length: query.length,
        platform_count: platformCount,
        platforms: platforms,
        deep_search_enabled: deepSearchEnabled,
    });
}

export function trackSearchResultsReceived(
    searchId: string,
    totalCount: number,
    platformBreakdown: Record<string, number>
): void {
    capturePostHog("search_results_count", {
        search_id: searchId,
        total_count: totalCount,
        ...platformBreakdown,
    });
}

export function trackSearchNoResults(searchId: string): void {
    capturePostHog("search_no_results", {
        search_id: searchId,
        source: "ui_search_results",
    });
}

export function trackPlatformFilterToggled(
    platform: string,
    enabled: boolean
): void {
    capturePostHog("platform_filter_toggled", {
        platform,
        enabled,
    });
}

export function trackDeepSearchToggled(enabled: boolean): void {
    capturePostHog("deep_search_toggled", {
        enabled,
        source: "ui_home_search_box",
    });
}

export function trackSearchResultClicked(
    searchId: string,
    platform: string,
    position: number,
    totalResults: number
): void {
    capturePostHog("search_result_clicked", {
        search_id: searchId,
        platform,
        position,
        total_results: totalResults,
        source: "ui_search_results_grid",
    });
}

// ============================================
// MEDIA/VIDEO ENGAGEMENT TRACKING
// ============================================

export function trackMediaCardHovered(
    mediaId: string,
    platform: string,
    hoverDurationMs: number
): void {
    capturePostHog("media_card_hovered", {
        media_id: mediaId,
        platform,
        hover_duration_ms: hoverDurationMs,
    });
}

export function trackMediaCardClicked(
    mediaId: string,
    platform: string,
    source: "search" | "board" | "history"
): void {
    capturePostHog("media_card_clicked", {
        media_id: mediaId,
        platform,
        source,
    });
}

export function trackVideoPlayStarted(
    mediaId: string,
    platform: string,
    duration: number | null
): void {
    capturePostHog("video_play_started", {
        media_id: mediaId,
        platform,
        video_duration_sec: duration,
    });
}

export function trackVideoPlayCompleted(
    mediaId: string,
    platform: string,
    watchDurationMs: number,
    totalDuration: number
): void {
    capturePostHog("video_play_completed", {
        media_id: mediaId,
        platform,
        watch_duration_ms: watchDurationMs,
        completion_percentage: (watchDurationMs / (totalDuration * 1000)) * 100,
    });
}

export function trackVideoMuteToggled(
    mediaId: string,
    platform: string,
    muted: boolean
): void {
    capturePostHog("video_mute_toggled", {
        media_id: mediaId,
        platform,
        muted,
    });
}

export function trackVideoTimelineScrubbed(
    mediaId: string,
    platform: string,
    fromPosition: number,
    toPosition: number,
    duration: number
): void {
    capturePostHog("video_timeline_scrubbed", {
        media_id: mediaId,
        platform,
        from_position_sec: fromPosition,
        to_position_sec: toPosition,
        duration_sec: duration,
        scrub_percentage: Math.abs((toPosition - fromPosition) / duration) * 100,
    });
}

export function trackMediaLoadFailed(
    mediaId: string,
    platform: string,
    errorType: string
): void {
    capturePostHog("media_load_failed", {
        media_id: mediaId,
        platform,
        error_type: errorType,
    });
}

// ============================================
// BOARD MANAGEMENT TRACKING
// ============================================

export function trackBoardCreated(boardId: string): void {
    capturePostHog("board_created", {
        board_id: boardId,
        source: "ui_boards",
    });
}

export function trackBoardViewed(boardId: string, itemCount: number): void {
    capturePostHog("board_viewed", {
        board_id: boardId,
        item_count: itemCount,
        source: "ui_boards",
    });
}

export function trackBoardItemAdded(
    boardId: string,
    mediaId: string,
    source: "search" | "history"
): void {
    capturePostHog("board_item_added", {
        board_id: boardId,
        media_id: mediaId,
        source,
    });
}

export function trackBoardItemRemoved(boardId: string, mediaId: string): void {
    capturePostHog("board_item_removed", {
        board_id: boardId,
        media_id: mediaId,
    });
}

export function trackBoardDeleted(boardId: string, itemCount: number): void {
    capturePostHog("board_deleted", {
        board_id: boardId,
        item_count: itemCount,
        source: "ui_boards",
    });
}

export function trackBoardInsightsGenerated(boardId: string, itemAnalyzed: number): void {
    capturePostHog("board_insights_generated", {
        board_id: boardId,
        items_analyzed: itemAnalyzed,
    });
}

// ============================================
// CONVERSION & PRICING TRACKING
// ============================================

export function trackPricingPageViewed(): void {
    capturePostHog("pricing_page_viewed", {
        source: "ui_billing_return",
    });
}

export function trackPlanClicked(
    productId: string,
    planName: string,
    isUpgrade: boolean
): void {
    capturePostHog("pricing_plan_clicked", {
        product_id: productId,
        plan_name: planName,
        is_upgrade: isUpgrade,
        source: "ui_billing_return",
    });
}

export function trackCheckoutStarted(
    productId: string,
    amount: number,
    currency: string
): void {
    capturePostHog("checkout_started", {
        product_id: productId,
        amount,
        currency,
        source: "ui_billing_return",
    });
}

export function trackCheckoutCompleted(
    productId: string,
    amount: number,
    currency: string
): void {
    capturePostHog("checkout_completed", {
        product_id: productId,
        amount,
        currency,
        source: "ui_billing_return",
    });
}

export function trackCheckoutFailed(
    productId: string,
    reason: string
): void {
    capturePostHog("checkout_failed", {
        product_id: productId,
        reason,
        source: "ui_billing_return",
    });
}

export function trackPlanUpgradeInitiated(
    fromProduct: string,
    toProduct: string
): void {
    capturePostHog("plan_upgrade_initiated", {
        from_product: fromProduct,
        to_product: toProduct,
        source: "ui_billing_return",
    });
}

export function trackPlanUpgradeCompleted(
    fromProduct: string,
    toProduct: string,
    amount: number
): void {
    capturePostHog("plan_upgrade_completed", {
        from_product: fromProduct,
        to_product: toProduct,
        amount,
        source: "ui_billing_return",
    });
}

export function trackPlanDowngradeScheduled(
    fromProduct: string,
    toProduct: string,
    effectiveDate: string | null
): void {
    capturePostHog("plan_downgrade_scheduled", {
        from_product: fromProduct,
        to_product: toProduct,
        effective_date: effectiveDate,
        source: "ui_billing_return",
    });
}

export function trackSubscriptionCancelled(reason: string | null = null): void {
    capturePostHog("subscription_cancelled", {
        reason,
        source: "ui_billing_return",
    });
}

export function trackSubscriptionRenewed(
    productId: string,
    amount: number,
    periodStart: string,
    periodEnd: string
): void {
    capturePostHog("subscription_renewed", {
        product_id: productId,
        amount,
        period_start: periodStart,
        period_end: periodEnd,
        source: "ui_billing_return",
    });
}

export function trackSubscriptionExpired(
    lastProduct: string | null
): void {
    capturePostHog("subscription_expired", {
        last_product: lastProduct,
    });
}

// ============================================
// ERROR & FRUSTRATION TRACKING
// ============================================

export function trackSearchApiFailed(
    searchId: string,
    platform: string,
    errorType: string
): void {
    capturePostHog("search_api_failed", {
        search_id: searchId,
        platform,
        error_type: errorType,
    });
}

export function trackNetworkTimeout(endpoint: string, timeoutMs: number): void {
    capturePostHog("network_timeout", {
        endpoint,
        timeout_ms: timeoutMs,
    });
}

export function trackPermissionDenied(resource: string, reason: string): void {
    capturePostHog("permission_denied", {
        resource,
        reason,
    });
}

// ============================================
// USER ONBOARDING TRACKING
// ============================================

export function trackUserFirstLogin(
    userId: string,
    daysFromSignup: number | null
): void {
    capturePostHog("user_first_login", {
        user_id: userId,
        days_from_signup: daysFromSignup,
    });
}

export function trackUserFirstSearch(userId: string): void {
    capturePostHog("user_first_search", {
        user_id: userId,
        source: "ui_search_results",
    });
}

export function trackUserFirstBoardCreated(userId: string): void {
    capturePostHog("user_first_board_created", {
        user_id: userId,
        source: "ui_boards",
    });
}

export function trackOnboardingAbandoned(
    flowId: string,
    step: number,
    totalSteps: number
): void {
    capturePostHog("onboarding_abandoned", {
        flow_id: flowId,
        step,
        total_steps: totalSteps,
    });
}

// ============================================
// FEATURE USAGE TRACKING
// ============================================

export function trackExportInitiated(
    itemId: string | null,
    itemType: "board" | "search" | "media"
): void {
    capturePostHog("export_initiated", {
        item_id: itemId,
        item_type: itemType,
    });
}

export function trackExportCompleted(
    itemId: string | null,
    itemType: "board" | "search" | "media",
    success: boolean,
    format: string
): void {
    capturePostHog("export_completed", {
        item_id: itemId,
        item_type: itemType,
        success,
        format,
    });
}

export function trackShareLinkCopied(
    itemType: "board" | "media",
    itemId: string | null
): void {
    capturePostHog("share_link_copied", {
        item_type: itemType,
        item_id: itemId,
    });
}

export function trackAnalyticsDashboardViewed(): void {
    capturePostHog("analytics_dashboard_viewed", {});
}

// ============================================
// SESSION & ENGAGEMENT TRACKING
// ============================================

export function trackSessionStarted(): void {
    capturePostHog("session_started", {
        source: "ui_app_bootstrap",
    });
}

export function trackSessionDurationMs(durationMs: number): void {
    capturePostHog("session_duration_ms", {
        duration_ms: durationMs,
        source: "ui_app_bootstrap",
    });
}

export function trackSearchResultsPageViewed(searchId: string): void {
    capturePostHog("search_results_page_viewed", {
        search_id: searchId,
        source: "ui_search_results",
    });
}

export function trackMediaDetailPageViewed(
    mediaId: string,
    platform: string
): void {
    capturePostHog("media_detail_page_viewed", {
        media_id: mediaId,
        platform,
    });
}
