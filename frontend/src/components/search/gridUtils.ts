// Hysteresis margin to prevent oscillation when scrollbar appears/disappears
const HYSTERESIS = 20;

// Breakpoints for column counts (ascending order)
const BREAKPOINTS = [
    { min: 1800, cols: 6 },
    { min: 1500, cols: 5 },
    { min: 1200, cols: 4 },
    { min: 900, cols: 3 },
    { min: 600, cols: 2 },
    { min: 0, cols: 1 },
];

/**
 * Get responsive column count with hysteresis to prevent oscillation.
 * 
 * When increasing columns: use exact breakpoint
 * When decreasing columns: require dropping HYSTERESIS px below the breakpoint
 * 
 * This prevents the "scrollbar dance" where:
 * 907px → 3 cols → scrollbar appears → 891px → 2 cols → scrollbar gone → 907px → repeat
 */
export function getResponsiveColumns(width: number, currentCols?: number): number {
    // Calculate what columns we'd get without hysteresis
    let targetCols = 1;
    for (const bp of BREAKPOINTS) {
        if (width >= bp.min) {
            targetCols = bp.cols;
            break;
        }
    }

    // If no current column count provided, just return the target
    if (currentCols === undefined) {
        return targetCols;
    }

    // If going UP in columns, allow it immediately
    if (targetCols > currentCols) {
        return targetCols;
    }

    // If going DOWN in columns, apply hysteresis
    // Find the breakpoint for the current column count
    const currentBreakpoint = BREAKPOINTS.find(bp => bp.cols === currentCols);
    if (currentBreakpoint && width >= currentBreakpoint.min - HYSTERESIS) {
        // Width hasn't dropped enough below the threshold, stay at current
        return currentCols;
    }

    return targetCols;
}
