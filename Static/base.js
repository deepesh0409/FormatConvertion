const startBtn = document.getElementById('startBtn');
let overlay = document.getElementById('processingOverlay');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');

if (startBtn) {
  startBtn.addEventListener('click', () => {
    if (!fileInput.files.length) {
      alert('Please upload a PDF first');
      return;
    }

    overlay.classList.remove('hidden');
    overlay.classList.add('flex');

    let progress = 0;
    progressBar.style.width = '0%';

    const stages = [
      'Uploading file…',
      'Extracting content…',
      'Running AI processing…',
      'Finalizing output…'
    ];

    let stageIndex = 0;

    const interval = setInterval(() => {
      progress += Math.floor(Math.random() * 10) + 5;
      if (progress >= 100) progress = 100;
      progressBar.style.width = progress + '%';

      if (stageIndex < stages.length) {
        progressText.innerText = stages[stageIndex];
        stageIndex++;
      }

      if (progress === 100) {
        clearInterval(interval);
        progressText.innerText = 'Completed';

        setTimeout(() => {
          overlay.classList.add('hidden');
          overlay.classList.remove('flex');
          progressBar.style.width = '0%';
        }, 800);
      }
    }, 600);
  });
}


if (dropZone && fileInput) {
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', e => {
        e.preventDefault();
        dropZone.classList.add('border-indigo-400');
    });
    
    // ... keep your other dropZone rules here ...

  dropZone.addEventListener('click', () => fileInput.click());

  dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('border-indigo-400');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-indigo-400');
  });

  dropZone.addEventListener('drop', e => {
    e.preventDefault();
    fileInput.files = e.dataTransfer.files;
    dropZone.classList.remove('border-indigo-400');
    dropZone.querySelector('p').innerText = fileInput.files[0].name;
  });

  fileInput.addEventListener('change', () => {
    dropZone.querySelector('p').innerText = fileInput.files[0].name;
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const mobileBtn = document.getElementById('mobile-menu-button');
  const mobileMenu = document.getElementById('mobile-menu');
  const iconOpen = document.getElementById('menu-icon-open');
  const iconClose = document.getElementById('menu-icon-close');

  if (mobileBtn && mobileMenu) {
    mobileBtn.addEventListener('click', () => {
      mobileMenu.classList.toggle('hidden');
      
      // Swap the hamburger and close icons
      if (iconOpen && iconClose) {
        iconOpen.classList.toggle('hidden');
        iconOpen.classList.toggle('block'); // Fixed typo here!
        iconClose.classList.toggle('hidden');
        iconClose.classList.toggle('block');
      }
    });
  }
});