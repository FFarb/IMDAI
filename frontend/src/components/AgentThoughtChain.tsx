import type { StreamEvent } from '../types/pipeline';

interface AgentThoughtChainProps {
    events: StreamEvent[];
    isActive: boolean;
}

export function AgentThoughtChain({ events, isActive }: AgentThoughtChainProps): JSX.Element {
    if (events.length === 0 && !isActive) {
        return <></>;
    }

    return (
        <div className="agent-thought-chain">
            <h3>🧠 Agent Thought Chain</h3>
            <div className="thought-timeline">
                {events.map((event, idx) => {
                    if (event.type === 'start') {
                        return (
                            <div key={idx} className="thought-item thought-start">
                                <div className="thought-icon">🚀</div>
                                <div className="thought-content">
                                    <div className="thought-title">Workflow Started</div>
                                    <div className="thought-message">{event.message}</div>
                                </div>
                            </div>
                        );
                    }

                    if (event.type === 'complete') {
                        return (
                            <div key={idx} className="thought-item thought-complete">
                                <div className="thought-icon">✅</div>
                                <div className="thought-content">
                                    <div className="thought-title">Workflow Complete</div>
                                    <div className="thought-message">{event.message}</div>
                                </div>
                            </div>
                        );
                    }

                    if (event.type === 'error') {
                        return (
                            <div key={idx} className="thought-item thought-error">
                                <div className="thought-icon">❌</div>
                                <div className="thought-content">
                                    <div className="thought-title">Error</div>
                                    <div className="thought-message">{event.message}</div>
                                </div>
                            </div>
                        );
                    }

                    if (event.type === 'agent_step') {
                        const agentIcons: Record<string, string> = {
                            vision: '👁️',
                            historian: '📚',
                            analyst: '🧠',
                            promptsmith: '✨',
                            critic: '🎯',
                            increment: '🔄',
                        };

                        const icon = agentIcons[event.agent] || '🤖';

                        return (
                            <div key={idx} className="thought-item thought-agent">
                                <div className="thought-icon">{icon}</div>
                                <div className="thought-content">
                                    <div className="thought-title">{event.agent_name}</div>
                                    {event.data?.message && (
                                        <div className="thought-message">{event.data.message}</div>
                                    )}
                                    {event.data?.count !== undefined && (
                                        <div className="thought-detail">Found: {event.data.count}</div>
                                    )}
                                    {event.data?.score !== undefined && (
                                        <div className="thought-detail">
                                            Score: {event.data.score}/10
                                            {event.data.decision && ` - ${event.data.decision}`}
                                        </div>
                                    )}
                                    {event.data?.iteration !== undefined && event.data.iteration > 0 && (
                                        <div className="thought-detail">Iteration: {event.data.iteration}</div>
                                    )}
                                </div>
                            </div>
                        );
                    }

                    return null;
                })}

                {isActive && events.length > 0 && events[events.length - 1].type !== 'complete' && (
                    <div className="thought-item thought-loading">
                        <div className="thought-icon">⏳</div>
                        <div className="thought-content">
                            <div className="thought-title">Processing...</div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
