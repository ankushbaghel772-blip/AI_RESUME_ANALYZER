/**
 * Drag and Drop & File Upload Interactive Handler.
 */

document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('resumeFileInput');
    const filePreview = document.getElementById('selectedFilePreview');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const fileSizeDisplay = document.getElementById('fileSizeDisplay');
    const submitBtn = document.getElementById('uploadSubmitBtn');
    const uploadForm = document.getElementById('resumeUploadForm');
    const loadingOverlay = document.getElementById('uploadLoadingOverlay');

    if (!dropzone || !fileInput) return;

    // Trigger file input click when dropzone is clicked
    dropzone.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag-and-drop event listeners
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateFilePreview(files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            updateFilePreview(fileInput.files[0]);
        }
    });

    function updateFilePreview(file) {
        if (!file) return;

        const validExts = ['.pdf', '.docx', '.txt'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();

        if (!validExts.includes(fileExt)) {
            alert("Unsupported file format! Please upload a PDF (.pdf), Word (.docx), or Text (.txt) file.");
            fileInput.value = '';
            if (filePreview) filePreview.style.display = 'none';
            return;
        }

        const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
        if (file.size > 5 * 1024 * 1024) {
            alert(`File size exceeds 5MB limit (${sizeInMB}MB). Please choose a smaller file.`);
            fileInput.value = '';
            if (filePreview) filePreview.style.display = 'none';
            return;
        }

        if (fileNameDisplay) fileNameDisplay.innerText = file.name;
        if (fileSizeDisplay) fileSizeDisplay.innerText = `${sizeInMB} MB`;
        if (filePreview) filePreview.style.display = 'flex';
    }

    if (uploadForm && submitBtn) {
        uploadForm.addEventListener('submit', () => {
            if (fileInput.files.length > 0) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Analyzing Resume with AI...';
                if (loadingOverlay) {
                    loadingOverlay.style.display = 'flex';
                }
            }
        });
    }
});
