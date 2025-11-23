import { useCallback, useState } from 'react';

interface ImageUploadProps {
    onImagesChange: (images: string[]) => void;
    images: string[];
}

export function ImageUpload({ onImagesChange, images }: ImageUploadProps): JSX.Element {
    const [isDragging, setIsDragging] = useState(false);
    const MAX_IMAGES = 5; // Prevent UI overload

    const handleFileChange = useCallback(
        async (files: FileList | null) => {
            if (!files || files.length === 0) return;

            const newImages: string[] = [];
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                if (!file.type.startsWith('image/')) continue;
                // Optional size guard – skip huge files (>5MB) to avoid memory blow‑up
                if (file.size > 5 * 1024 * 1024) continue;
                const reader = new FileReader();
                const base64Promise = new Promise<string>((resolve) => {
                    reader.onload = (e) => {
                        const result = e.target?.result as string;
                        resolve(result);
                    };
                    reader.readAsDataURL(file);
                });
                const base64 = await base64Promise;
                newImages.push(base64);
                // Stop early if we already hit the limit
                if (images.length + newImages.length >= MAX_IMAGES) break;
            }
            // Combine with existing, respecting the max limit
            const combined = [...images, ...newImages].slice(0, MAX_IMAGES);
            onImagesChange(combined);
        },
        [images, onImagesChange]
    );

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            setIsDragging(false);
            handleFileChange(e.dataTransfer.files);
        },
        [handleFileChange]
    );

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback(() => {
        setIsDragging(false);
    }, []);

    const removeImage = useCallback(
        (index: number) => {
            const newImages = images.filter((_, i) => i !== index);
            onImagesChange(newImages);
        },
        [images, onImagesChange]
    );

    // Reset the hidden file input after each selection so the same file can be re‑selected
    const resetFileInput = (input: HTMLInputElement) => {
        input.value = '';
    };

    return (
        <div className="image-upload">
            <label className="field-label">Reference Images (Optional)</label>
            <p className="field-hint">Upload images to guide the AI agents (max {MAX_IMAGES})</p>

            <div
                className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
            >
                <input
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={(e) => {
                        handleFileChange(e.target.files);
                        resetFileInput(e.target);
                    }}
                    style={{ display: 'none' }}
                    id="image-upload-input"
                />
                <label htmlFor="image-upload-input" className="upload-label">
                    <div className="upload-icon">📸</div>
                    <div className="upload-text">
                        {images.length === 0 ? (
                            <>
                                <strong>Drop images here</strong> or click to browse
                            </>
                        ) : (
                            <>
                                <strong>{images.length} image(s) uploaded</strong> - Add more or click to replace
                            </>
                        )}
                    </div>
                </label>
            </div>

            {images.length > 0 && (
                <div className="uploaded-images">
                    {images.map((img, idx) => (
                        <div key={idx} className="uploaded-image">
                            <img src={img} alt={`Reference ${idx + 1}`} />
                            <button
                                type="button"
                                className="remove-image"
                                onClick={() => removeImage(idx)}
                                aria-label="Remove image"
                            >
                                ×
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
