import EXIF from 'exif-js';

/**
 * Strips metadata from an image file.
 * Returns a new File object without metadata.
 */
export const scrubImage = async (file) => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);

                // Re-exporting as blob strips EXIF
                canvas.toBlob((blob) => {
                    const newFile = new File([blob], file.name, {
                        type: file.type,
                        lastModified: Date.now(),
                    });
                    resolve(newFile);
                }, file.type, 1.0);
            };
            img.onerror = reject;
            img.src = e.target.result;
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
};

/**
 * Gets metadata from an image file using EXIF.js
 */
export const getMetadata = (file) => {
    return new Promise((resolve) => {
        if (!file.type.startsWith('image/')) {
            resolve(null);
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            const arrayBuffer = e.target.result;
            const metadata = EXIF.readFromBinaryFile(arrayBuffer);

            if (!metadata) {
                resolve(null);
                return;
            }

            // Filter and clean metadata for display
            const cleanMetadata = {};
            const interestingTags = [
                'Make', 'Model', 'Software', 'DateTime',
                'GPSLatitude', 'GPSLongitude', 'Artist', 'Copyright',
                'ExifVersion', 'XResolution', 'YResolution'
            ];

            interestingTags.forEach(tag => {
                if (metadata[tag]) {
                    cleanMetadata[tag] = metadata[tag].toString();
                }
            });

            resolve(Object.keys(cleanMetadata).length > 0 ? cleanMetadata : null);
        };
        reader.readAsArrayBuffer(file);
    });
};
