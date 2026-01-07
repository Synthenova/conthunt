export function getResponsiveColumns(width: number): number {
    let nextCols = 1;
    if (width >= 1800) nextCols = 6;
    else if (width >= 1500) nextCols = 5;
    else if (width >= 1200) nextCols = 4;
    else if (width >= 900) nextCols = 3;
    else if (width >= 600) nextCols = 2;
    return nextCols;
}
