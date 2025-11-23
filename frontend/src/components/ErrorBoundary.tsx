import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            return this.props.fallback || (
                <div style={{
                    padding: '2rem',
                    margin: '2rem',
                    border: '2px solid #ef4444',
                    borderRadius: '8px',
                    backgroundColor: '#fef2f2',
                    color: '#991b1b',
                    fontFamily: 'system-ui, sans-serif'
                }}>
                    <h2 style={{ marginTop: 0 }}>Something went wrong.</h2>
                    <p>The application encountered an error. Please try reloading the page.</p>
                    <details style={{ whiteSpace: 'pre-wrap', marginTop: '1rem', padding: '1rem', background: 'rgba(0,0,0,0.05)', borderRadius: '4px' }}>
                        <summary style={{ cursor: 'pointer', marginBottom: '0.5rem' }}>Error Details</summary>
                        {this.state.error && this.state.error.toString()}
                    </details>
                    <button
                        onClick={() => window.location.reload()}
                        style={{
                            marginTop: '1rem',
                            padding: '0.5rem 1rem',
                            backgroundColor: '#ef4444',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '1rem'
                        }}
                    >
                        Reload Page
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}
