declare global {
    namespace JSX {
        interface IntrinsicElements {
            "lord-icon": React.DetailedHTMLProps<
                React.HTMLAttributes<HTMLElement>,
                HTMLElement
            > & {
                src?: string;
                trigger?: string;
                colors?: string;
                state?: string;
                style?: React.CSSProperties;
            };
        }
    }
}
export { };
