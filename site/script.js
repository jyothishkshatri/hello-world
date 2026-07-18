const remoteImageMap = {
  "assets/tiger.svg": "https://images.unsplash.com/photo-1561731216-c3a4d99437d5?auto=format&fit=crop&w=1200&q=85",
  "assets/valley.svg": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=85",
  "assets/community.svg": "https://images.unsplash.com/photo-1542810634-71277d95dcbb?auto=format&fit=crop&w=1200&q=85",
  "assets/baby-elephant.svg": "https://images.unsplash.com/photo-1557050543-4d5f4e07ef46?auto=format&fit=crop&w=1200&q=85"
};

document.querySelectorAll("img[src]").forEach((image) => {
  const source = image.getAttribute("src");
  if (remoteImageMap[source]) image.src = remoteImageMap[source];
});

(() => {
  const header = document.querySelector('[data-header]');
  const menuToggle = document.querySelector('[data-menu-toggle]');
  const nav = document.querySelector('[data-nav]');
  const storyModal = document.querySelector('[data-story-modal]');
  const donateModal = document.querySelector('[data-donate-modal]');
  const toast = document.querySelector('[data-toast]');
  let lastFocused = null;
  let selectedAmount = 75;
  let selectedFrequency = 'monthly';

  const setHeaderState = () => {
    header?.classList.toggle('is-scrolled', window.scrollY > 24);
  };

  const closeMenu = () => {
    nav?.classList.remove('is-open');
    menuToggle?.setAttribute('aria-expanded', 'false');
    menuToggle?.setAttribute('aria-label', 'Open navigation');
  };

  menuToggle?.addEventListener('click', () => {
    const open = menuToggle.getAttribute('aria-expanded') === 'true';
    menuToggle.setAttribute('aria-expanded', String(!open));
    menuToggle.setAttribute('aria-label', open ? 'Open navigation' : 'Close navigation');
    nav?.classList.toggle('is-open', !open);
  });

  nav?.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));
  window.addEventListener('scroll', setHeaderState, { passive: true });
  setHeaderState();

  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.14, rootMargin: '0px 0px -35px' });

  document.querySelectorAll('[data-reveal]').forEach((element) => revealObserver.observe(element));

  const formatCounter = (value, decimals = 0) => {
    if (decimals > 0) return `${value.toFixed(decimals)}M+`;
    if (value >= 1000) return `${Math.round(value).toLocaleString()}+`;
    return `${Math.round(value)}+`;
  };

  const animateCounter = (element) => {
    const target = Number(element.dataset.counter || 0);
    const decimals = Number(element.dataset.decimals || 0);
    const duration = 1500;
    const start = performance.now();

    const frame = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      element.textContent = formatCounter(target * eased, decimals);
      if (progress < 1) requestAnimationFrame(frame);
    };

    requestAnimationFrame(frame);
  };

  const counterObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      animateCounter(entry.target);
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.65 });

  document.querySelectorAll('[data-counter]').forEach((counter) => counterObserver.observe(counter));

  const openModal = (modal) => {
    if (!modal) return;
    lastFocused = document.activeElement;
    modal.showModal();
    document.body.classList.add('modal-open');
    modal.querySelector('button, [href], input')?.focus();
  };

  const closeModal = (modal) => {
    if (!modal?.open) return;
    modal.close();
    document.body.classList.remove('modal-open');
    lastFocused?.focus?.();
  };

  document.querySelectorAll('[data-open-story]').forEach((button) => {
    button.addEventListener('click', () => openModal(storyModal));
  });

  const frequencyLabel = () => selectedFrequency === 'monthly' ? 'monthly' : 'one time';
  const receiptLabel = () => selectedFrequency === 'monthly' ? `$${selectedAmount} / month` : `$${selectedAmount} once`;

  const updateDonationCopy = () => {
    const summary = `Give $${selectedAmount} ${frequencyLabel()}`;
    document.querySelectorAll('[data-donate-summary]').forEach((button) => { button.textContent = summary; });
    document.querySelectorAll('[data-modal-amount]').forEach((node) => { node.textContent = `$${selectedAmount} ${frequencyLabel()}`; });
    document.querySelectorAll('[data-modal-amount-receipt]').forEach((node) => { node.textContent = receiptLabel(); });
  };

  document.querySelectorAll('[data-frequency]').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelectorAll('[data-frequency]').forEach((item) => item.classList.remove('is-active'));
      button.classList.add('is-active');
      selectedFrequency = button.dataset.frequency;
      updateDonationCopy();
    });
  });

  const customAmountInput = document.querySelector('[data-custom-amount]');
  document.querySelectorAll('[data-amount]').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelectorAll('[data-amount]').forEach((item) => item.classList.remove('is-active'));
      button.classList.add('is-active');
      selectedAmount = Number(button.dataset.amount);
      if (customAmountInput) customAmountInput.value = '';
      updateDonationCopy();
    });
  });

  customAmountInput?.addEventListener('input', () => {
    const parsed = Math.max(1, Math.round(Number(customAmountInput.value) || 0));
    if (!parsed) return;
    document.querySelectorAll('[data-amount]').forEach((item) => item.classList.remove('is-active'));
    selectedAmount = parsed;
    updateDonationCopy();
  });

  document.querySelectorAll('[data-open-donate]').forEach((button) => {
    button.addEventListener('click', () => {
      closeMenu();
      updateDonationCopy();
      openModal(donateModal);
    });
  });

  document.querySelectorAll('[data-close-modal]').forEach((button) => {
    button.addEventListener('click', () => closeModal(button.closest('dialog')));
  });

  [storyModal, donateModal].forEach((modal) => {
    modal?.addEventListener('click', (event) => {
      const box = modal.getBoundingClientRect();
      const inside = event.clientX >= box.left && event.clientX <= box.right && event.clientY >= box.top && event.clientY <= box.bottom;
      if (!inside) closeModal(modal);
    });
    modal?.addEventListener('cancel', (event) => {
      event.preventDefault();
      closeModal(modal);
    });
  });

  const showToast = (message) => {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('is-visible');
    window.setTimeout(() => toast.classList.remove('is-visible'), 3500);
  };

  document.querySelector('[data-confirm-demo]')?.addEventListener('click', () => {
    closeModal(donateModal);
    showToast(`Thank you. Your $${selectedAmount} ${frequencyLabel()} demo gift is complete.`);
  });

  const newsletter = document.querySelector('[data-newsletter]');
  const newsletterStatus = document.querySelector('[data-newsletter-status]');
  newsletter?.addEventListener('submit', (event) => {
    event.preventDefault();
    const email = newsletter.querySelector('input[type="email"]');
    if (!email?.checkValidity()) {
      newsletterStatus.textContent = 'Please enter a valid email address.';
      email?.focus();
      return;
    }
    newsletterStatus.textContent = 'Welcome to the wild—your first hopeful story is on its way.';
    newsletter.reset();
  });
})();
