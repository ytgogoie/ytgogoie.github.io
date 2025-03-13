document.addEventListener('DOMContentLoaded', function() {
    const urlForm = document.getElementById('url-form');
    const loadingSpinner = document.getElementById('loading');
    const videoInfo = document.getElementById('video-info');
    const errorMessage = document.getElementById('error-message');
    const videoThumbnail = document.getElementById('video-thumbnail');
    const videoTitle = document.getElementById('video-title');
    const videoDuration = document.getElementById('video-duration');
    const formatList = document.getElementById('format-list');
    const faqItems = document.querySelectorAll('.faq-item');

    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    const moonIcon = themeToggle.querySelector('.dark\\:hidden');
    const sunIcon = themeToggle.querySelector('.hidden.dark\\:block');

    // Check for saved theme preference or use device preference
    const isDarkMode = localStorage.getItem('darkMode') === 'true' || 
                       (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);

    // Apply the theme on initial load
    if (isDarkMode) {
        document.documentElement.classList.add('dark');
        moonIcon.classList.add('hidden');
        sunIcon.classList.remove('hidden');
    } else {
        document.documentElement.classList.remove('dark');
        moonIcon.classList.remove('hidden');
        sunIcon.classList.add('hidden');
    }

    // Toggle theme when button is clicked
    themeToggle.addEventListener('click', () => {
        // Toggle dark class on html element
        const isDarkModeNow = document.documentElement.classList.toggle('dark');
        
        // Toggle visibility of sun/moon icons
        if (isDarkModeNow) {
            moonIcon.classList.add('hidden');
            sunIcon.classList.remove('hidden');
        } else {
            moonIcon.classList.remove('hidden');
            sunIcon.classList.add('hidden');
        }
        
        // Save preference to localStorage
        localStorage.setItem('darkMode', isDarkModeNow);
    });
    
    // Initialize FAQ accordion functionality
    if (faqItems && faqItems.length) {
        faqItems.forEach(item => {
            const question = item.querySelector('.faq-question');
            const answer = item.querySelector('.faq-answer');
            const icon = question.querySelector('svg');
            
            // Set the first FAQ item to be expanded by default
            if (item === faqItems[0]) {
                answer.classList.remove('hidden');
                icon.classList.add('rotate-180');
                item.classList.add('shadow-md');
                item.classList.add('bg-gray-100');
                item.classList.add('dark:bg-gray-600');
            }
            
            question.addEventListener('click', () => {
                const isOpen = !answer.classList.contains('hidden');
                
                // Close all FAQs
                faqItems.forEach(otherItem => {
                    const otherAnswer = otherItem.querySelector('.faq-answer');
                    const otherIcon = otherItem.querySelector('.faq-question svg');
                    
                    otherAnswer.classList.add('hidden');
                    otherIcon.classList.remove('rotate-180');
                    otherItem.classList.remove('shadow-md');
                    otherItem.classList.remove('bg-gray-100');
                    otherItem.classList.remove('dark:bg-gray-600');
                });
                
                // If the clicked FAQ was closed, open it
                if (!isOpen) {
                    answer.classList.remove('hidden');
                    icon.classList.add('rotate-180');
                    item.classList.add('shadow-md');
                    item.classList.add('bg-gray-100');
                    item.classList.add('dark:bg-gray-600');
                }
            });
        });
    }

    if (urlForm) {
        urlForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const url = document.getElementById('url').value.trim();

            // Reset UI state
            videoInfo.classList.add('hidden');
            errorMessage.classList.add('hidden');
            loadingSpinner.classList.remove('hidden');
            formatList.innerHTML = '';

            try {
                // Create form data for the request
                const formData = new FormData();
                formData.append('url', url);

                // Fetch video information
                const response = await fetch('/fetch-info', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    // Display video information
                    videoThumbnail.loading = "lazy";
                    videoThumbnail.src = data.thumbnail;
                    videoTitle.textContent = data.title;
                    videoDuration.textContent = formatDuration(data.duration);

                    // Populate formats
                    data.formats.forEach(format => {
                        const formatItem = document.createElement('div');
                        formatItem.className = 'format-button bg-white dark:bg-gray-700 rounded-lg shadow-md p-4 border border-gray-200 dark:border-gray-600 hover:border-red-500 dark:hover:border-red-500 transition-all duration-200';

                        // Get filesize from the format data
                        const fileSizeMB = format.filesize || 'Unknown';

                        let formatHTML = `
                            <div class="flex flex-col justify-between h-full">
                                <div class="format-container mb-3">
                                    <div class="flex items-center mb-2">
                                        <span class="format-quality text-gray-900 dark:text-white font-medium">${format.quality}</span>
                                    </div>
                                    <div class="flex flex-wrap gap-2">
                                        <span class="format-badge bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 text-xs px-2 py-1 rounded">${format.extension}</span>
                                        <span class="format-badge bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 text-xs px-2 py-1 rounded">${fileSizeMB}</span>
                                        ${(!format.has_audio && !url.includes('/shorts/')) ? `<span class="format-badge bg-red-200 dark:bg-red-900 text-red-800 dark:text-red-200 text-xs px-2 py-1 rounded font-semibold">No Audio</span>` : ''}
                                    </div>
                                </div>
                                <button class="download-format-button w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg flex items-center justify-center space-x-2">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                                    </svg>
                                    <span>Download</span>
                                </button>
                            </div>
                        `;

                        formatItem.innerHTML = formatHTML;
                        formatList.appendChild(formatItem);

                        // Add click event to download button
                        const downloadButton = formatItem.querySelector('.download-format-button');
                        downloadButton.addEventListener('click', function() {
                            downloadVideo(url, format.format_id, data.title);
                        });
                    });

                    // Show video info section
                    videoInfo.classList.remove('hidden');
                } else {
                    // Show error message
                    showError(data.error || 'An error occurred while fetching video information.');
                }
            } catch (error) {
                console.error('Error:', error);
                showError('An unexpected error occurred. Please try again.');
            } finally {
                loadingSpinner.classList.add('hidden');
            }
        });
    }

    function downloadVideo(url, formatId, videoTitle) {
        // Create a form to submit the download request
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/download';

        // URL input
        const urlInput = document.createElement('input');
        urlInput.type = 'hidden';
        urlInput.name = 'url';
        urlInput.value = url;

        // Format input
        const formatInput = document.createElement('input');
        formatInput.type = 'hidden';
        formatInput.name = 'format';
        formatInput.value = formatId;

        // Video Title input (added for potential server-side use)
        const titleInput = document.createElement('input');
        titleInput.type = 'hidden';
        titleInput.name = 'title';
        titleInput.value = videoTitle;


        form.appendChild(urlInput);
        form.appendChild(formatInput);
        form.appendChild(titleInput);
        document.body.appendChild(form);

        form.submit();
        document.body.removeChild(form);
    }

    function showError(message) {
        errorMessage.querySelector('span').textContent = message;
        errorMessage.classList.remove('hidden');
    }

    function formatDuration(seconds) {
        if (!seconds) return null;

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        let result = '';

        if (hours > 0) {
            result += `${hours}h `;
        }

        if (minutes > 0 || hours > 0) {
            result += `${minutes}m `;
        }

        result += `${secs}s`;

        return result;
    }
});