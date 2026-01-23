/**
 * Tutorial Target Selectors
 * 
 * Maps flow step IDs to their target element selectors.
 * Targets are managed here in the frontend for better separation of concerns.
 * 
 * Format: "flowId.stepId" -> "CSS selector"
 * 
 * Use data-tutorial attributes on elements:
 *   <div data-tutorial="search_input">...</div>
 * 
 * Then reference here as:
 *   "home_tour.search_input": "[data-tutorial='search_input']"
 */

export type TutorialTargetKey = `${string}.${string}`;

export const TUTORIAL_TARGETS: Record<TutorialTargetKey, string> = {
    // Home Tour
    "home_tour.search_input": "[data-tutorial='search_input']",
    "home_tour.send_button": "[data-tutorial='send_button']",

    // Chat Tour
    "chat_tour.intro": "[data-tutorial='chat_sidebar']",
    "chat_tour.canvas": "[data-tutorial='chat_canvas']",
    "chat_tour.tabs": "[data-tutorial='chat_tabs']",
    "chat_tour.video_click": "[data-tutorial='video_card']:first-of-type",
    "chat_tour.analyse": "[data-tutorial='analyse_button']",
    "chat_tour.select_videos": "[data-tutorial='video_checkbox']:first-of-type",
    "chat_tour.selection_bar": "[data-tutorial='selection_bar']",

    // Boards Tour (list page)
    "boards_tour.click_board": "[data-tutorial='board_card']:first-of-type",

    // Board Detail Tour
    "board_detail_tour.videos_tab": "[data-tutorial='videos_tab']",
    "board_detail_tour.insights_tab": "[data-tutorial='insights_tab']",
    "board_detail_tour.refresh_insights": "[data-tutorial='refresh_insights']",

    // Profile Tour
    "profile_tour.streak": "[data-tutorial='streak_section']",
};

/**
 * Get the target selector for a tutorial step
 */
export function getTutorialTarget(flowId: string, stepId: string): string | null {
    const key = `${flowId}.${stepId}` as TutorialTargetKey;
    return TUTORIAL_TARGETS[key] ?? null;
}

/**
 * Preferred tooltip position for certain steps
 * Returns null to use automatic positioning
 */
export const TUTORIAL_POSITIONS: Partial<Record<TutorialTargetKey, "top" | "bottom" | "left" | "right">> = {
    "home_tour.search_input": "top",
    "home_tour.send_button": "top",
    "chat_tour.intro": "left",
    "chat_tour.tabs": "bottom",
};

export function getTutorialPosition(flowId: string, stepId: string): "top" | "bottom" | "left" | "right" | null {
    const key = `${flowId}.${stepId}` as TutorialTargetKey;
    return TUTORIAL_POSITIONS[key] ?? null;
}

/**
 * Interaction type that completes a step
 */
export type InteractionType = 'click' | 'focus' | 'input' | 'submit' | 'next_button';

/**
 * Mapping of steps to interaction types
 */
export const TUTORIAL_INTERACTIONS: Partial<Record<TutorialTargetKey, InteractionType>> = {
    // Home
    "home_tour.search_input": "next_button", // Explicit next button required
    "home_tour.send_button": "click",

    // Chat
    "chat_tour.intro": "next_button",
    "chat_tour.canvas": "next_button",
    "chat_tour.tabs": "next_button",
    "chat_tour.select_videos": "click",
    "chat_tour.selection_bar": "next_button",
    "chat_tour.video_click": "click",
    "chat_tour.analyse": "click",

    // Boards
    "boards_tour.click_board": "click",

    // Board Detail
    "board_detail_tour.videos_tab": "next_button",
    "board_detail_tour.insights_tab": "click",
    "board_detail_tour.refresh_insights": "click",

    // Profile
    "profile_tour.streak": "next_button",
};

export function getTutorialInteraction(flowId: string, stepId: string): InteractionType {
    const key = `${flowId}.${stepId}` as TutorialTargetKey;
    return TUTORIAL_INTERACTIONS[key] ?? "next_button";
}
