import { useState, useEffect } from 'react';

interface GenerationItem {
    id: string;
    path: string;
    preview: string | null;
    has_master: boolean;
    has_vector: boolean;
    metadata: any;
}

interface LibraryStructure {
    [date: string]: {
        [strategy: string]: GenerationItem[];
    };
}

export function LibraryTab() {
    const [library, setLibrary] = useState<LibraryStructure>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchLibrary();
    }, []);

    const fetchLibrary = async () => {
        try {
            setLoading(true);
            const response = await fetch('http://localhost:8000/api/library');
            if (!response.ok) throw new Error('Failed to fetch library');
            const data = await response.json();
            setLibrary(data.data || {});
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const handleAction = async (generationId: string, actionType: string) => {
        try {
            const response = await fetch('http://localhost:8000/api/library/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ generation_id: parseInt(generationId), action_type: actionType }),
            });
            if (!response.ok) throw new Error('Failed to mark action');
            // Optionally refresh library or show success message
        } catch (err) {
            console.error('Action failed:', err);
        }
    };

    if (loading) {
        return (
            <section className="card">
                <header className="card-header">
                    <h2>Library</h2>
                </header>
                <div style={{ padding: '2rem', textAlign: 'center' }}>Loading library...</div>
            </section>
        );
    }

    if (error) {
        return (
            <section className="card">
                <header className="card-header">
                    <h2>Library</h2>
                </header>
                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--error)' }}>
                    Error: {error}
                </div>
            </section>
        );
    }

    const dates = Object.keys(library).sort().reverse();

    return (
        <section className="card">
            <header className="card-header">
                <div>
                    <h2>Library</h2>
                    <p className="card-subtitle">Browse your generated designs</p>
                </div>
                <button onClick={fetchLibrary} className="btn-secondary">
                    Refresh
                </button>
            </header>

            <div style={{ padding: '1.5rem' }}>
                {dates.length === 0 ? (
                    <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                        No designs yet. Generate some to see them here!
                    </p>
                ) : (
                    dates.map((date) => (
                        <div key={date} style={{ marginBottom: '2rem' }}>
                            <h3 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>{date}</h3>
                            {Object.entries(library[date]).map(([strategyName, generations]) => (
                                <div key={strategyName} style={{ marginBottom: '1.5rem' }}>
                                    <h4 style={{ marginBottom: '0.75rem', textTransform: 'capitalize' }}>
                                        {strategyName.replace(/-/g, ' ')}
                                    </h4>
                                    <div
                                        style={{
                                            display: 'grid',
                                            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                                            gap: '1rem',
                                        }}
                                    >
                                        {generations.map((gen) => (
                                            <div
                                                key={gen.id}
                                                style={{
                                                    border: '1px solid var(--border)',
                                                    borderRadius: '8px',
                                                    overflow: 'hidden',
                                                    background: 'var(--surface)',
                                                }}
                                            >
                                                {gen.preview && (
                                                    <img
                                                        src={`http://localhost:8000${gen.preview.replace(/\\/g, '/').replace('data/library', '/library')}`}
                                                        alt={`Generation ${gen.id}`}
                                                        style={{ width: '100%', height: '200px', objectFit: 'cover' }}
                                                    />
                                                )}
                                                <div style={{ padding: '0.75rem' }}>
                                                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                                        <button
                                                            onClick={() => handleAction(gen.id, 'saved')}
                                                            className="btn-secondary"
                                                            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                                                        >
                                                            ⭐ Save
                                                        </button>
                                                        {!gen.has_master && (
                                                            <button
                                                                onClick={() => handleAction(gen.id, 'upscaled')}
                                                                className="btn-secondary"
                                                                style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                                                            >
                                                                🔍 Upscale
                                                            </button>
                                                        )}
                                                        {!gen.has_vector && (
                                                            <button
                                                                onClick={() => handleAction(gen.id, 'vectorized')}
                                                                className="btn-secondary"
                                                                style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                                                            >
                                                                📐 Vectorize
                                                            </button>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ))
                )}
            </div>
        </section>
    );
}
