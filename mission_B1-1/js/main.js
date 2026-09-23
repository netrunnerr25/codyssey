'use strict';

const GITHUB_USERNAME = 'netrunnerr25';
const PROJECT_REPOSITORIES = ['travel-maker-backend', 'edu-platform-integrated'];
const PROJECT_LABELS = {
  'travel-maker-backend': { title: 'Travel Maker', category: '여행 추천', symbol: '↗' },
  'edu-platform-integrated': { title: 'Edu Platform', category: '교육 관리', symbol: '▤' },
};
const HEADER_SCROLL_THRESHOLD = 60;
const TOP_BUTTON_THRESHOLD = 300;
const REVEAL_THRESHOLD = 0.2;
const fields = ['name', 'email', 'message'];
const state = {
  theme: 'light',
  projects: { status: 'loading', items: [], error: '' },
  formErrors: { name: '', email: '', message: '' },
  formSuccess: '',
  menuOpen: false,
  scrolled: false,
  showTopButton: false,
};

const header = document.querySelector('.site-header');
const menuButton = document.querySelector('#menu-toggle');
const menu = document.querySelector('#nav-menu');
const themeButton = document.querySelector('#theme-toggle');
const topButton = document.querySelector('#back-to-top');
const projectGrid = document.querySelector('#projects-grid');
const projectStatus = document.querySelector('#projects-status');
const retryButton = document.querySelector('#retry-projects');
const form = document.querySelector('#contact-form');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

// API 문자열은 템플릿에 넣기 전에 항상 이스케이프한다.
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[character]));

const renderTheme = () => {
  const dark = state.theme === 'dark';
  document.documentElement.dataset.theme = state.theme;
  themeButton.setAttribute('aria-pressed', String(dark));
  themeButton.setAttribute('aria-label', dark ? '라이트 모드 켜기' : '다크 모드 켜기');
  document.querySelector('#theme-icon').textContent = dark ? '☀' : '☾';
};

const renderMenu = () => {
  menu.classList.toggle('active', state.menuOpen);
  menuButton.setAttribute('aria-expanded', String(state.menuOpen));
  menuButton.setAttribute('aria-label', state.menuOpen ? '메뉴 닫기' : '메뉴 열기');
  menuButton.firstElementChild.textContent = state.menuOpen ? '×' : '☰';
};

const renderScroll = () => {
  if (state.scrolled) header.classList.add('scrolled');
  else header.classList.remove('scrolled');
  topButton.hidden = !state.showTopButton;
};

const renderProjects = () => {
  const { status, items, error } = state.projects;
  projectGrid.setAttribute('aria-busy', String(status === 'loading'));
  projectStatus.classList.toggle('is-error', status === 'error');
  retryButton.hidden = status !== 'error';
  const messages = {
    loading: '프로젝트를 불러오는 중입니다…',
    success: `프로젝트 ${items.length}개`,
    empty: '표시할 프로젝트가 없습니다.',
    error,
  };
  projectStatus.textContent = messages[status];
  projectGrid.innerHTML = items.map((project) => {
    const { name, description, language, stargazers_count, forks_count } = project;
    const { title, category, symbol } = PROJECT_LABELS[name];
    // 외부 URL을 그대로 삽입하지 않고 고정된 GitHub 도메인으로 구성한다.
    const url = `https://github.com/${encodeURIComponent(GITHUB_USERNAME)}/${encodeURIComponent(name)}`;
    return `<article class="project-card">
      <div class="project-cover"><span class="project-symbol" aria-hidden="true">${escapeHTML(symbol)}</span><span>${escapeHTML(category)}</span></div>
      <h3><a href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer" aria-label="${escapeHTML(name)} GitHub 저장소 (새 탭)">${escapeHTML(title)} <span aria-hidden="true">↗</span></a></h3>
      <p class="repository-name">${escapeHTML(name)}</p>
      <p>${escapeHTML(description || '등록된 설명이 없습니다.')}</p>
      <div class="project-meta"><span class="project-language">${escapeHTML(language || '언어 정보 없음')}</span><span aria-label="스타 ${escapeHTML(stargazers_count ?? 0)}개">☆ ${escapeHTML(stargazers_count ?? 0)}</span><span aria-label="포크 ${escapeHTML(forks_count ?? 0)}개">⑂ ${escapeHTML(forks_count ?? 0)}</span></div>
    </article>`;
  }).join('');
};

const loadProjects = async () => {
  state.projects = { status: 'loading', items: [], error: '' };
  renderProjects();
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 15000);
  try {
    const repositories = [];
    let page = 1;
    // 사용자 저장소 목록에서 지정한 프로젝트를 찾는다. 한 번에 최대 100개 조회.
    while (true) {
      const response = await fetch(`https://api.github.com/users/${GITHUB_USERNAME}/repos?sort=updated&per_page=100&page=${page}`, {
        signal: controller.signal,
        headers: { Accept: 'application/vnd.github+json' },
      });
      if (response.status === 403 || response.status === 429) {
        throw new Error('프로젝트를 불러올 수 없습니다. GitHub API 요청 한도를 초과했습니다(시간당 60회). 잠시 후 다시 시도해주세요.');
      }
      if (!response.ok) throw new Error('프로젝트를 불러올 수 없습니다. 다시 시도해주세요.');
      const batch = await response.json();
      if (!Array.isArray(batch)) throw new Error('프로젝트를 불러올 수 없습니다. GitHub 응답을 확인해주세요.');
      repositories.push(...batch);
      const foundAll = PROJECT_REPOSITORIES.every((name) => repositories.some((project) => project.name === name));
      if (foundAll || batch.length < 100) break;
      page += 1;
    }
    const items = repositories
      // 직접 지정한 프로젝트는 fork 여부와 관계없이 포함한다.
      .filter((project) => project && PROJECT_REPOSITORIES.includes(project.name) && !project.archived)
      .sort((first, second) => new Date(second.updated_at) - new Date(first.updated_at))
      .slice(0, 2);
    state.projects = { status: items.length ? 'success' : 'empty', items, error: '' };
  } catch (error) {
    const message = error.name === 'AbortError'
      ? '프로젝트를 불러올 수 없습니다. 요청 시간이 초과되었습니다. 다시 시도해주세요.'
      : error instanceof TypeError
        ? '프로젝트를 불러올 수 없습니다. 네트워크 연결을 확인하고 다시 시도해주세요.'
        : error.message;
    state.projects = { status: 'error', items: [], error: message };
  } finally {
    window.clearTimeout(timeout);
    renderProjects();
  }
};

const validateField = (field) => {
  const value = form.elements.namedItem(field).value.trim();
  if (!value) return { name: '이름을 입력해주세요.', email: '이메일을 입력해주세요.', message: '메시지를 입력해주세요.' }[field];
  if (field === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return '올바른 이메일 형식을 입력해주세요.';
  return '';
};

const renderForm = () => {
  fields.forEach((field) => {
    const error = state.formErrors[field];
    form.elements.namedItem(field).setAttribute('aria-invalid', String(Boolean(error)));
    document.querySelector(`#${field}-error`).textContent = error;
  });
  document.querySelector('#form-status').textContent = state.formSuccess;
  if (state.formSuccess) form.reset();
};

const scrollToSection = (target) => {
  target.scrollIntoView({ behavior: reducedMotion.matches ? 'instant' : 'smooth', block: 'start' });
  // 앵커 목적지에 키보드 포커스도 함께 전달한다.
  if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
  target.focus({ preventScroll: true });
};

// 사용자 이벤트 → state 변경 → render 함수 → DOM 변경.
menuButton.addEventListener('click', () => {
  state.menuOpen = !state.menuOpen;
  renderMenu();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && state.menuOpen) {
    state.menuOpen = false;
    renderMenu();
    menuButton.focus();
  }
});
window.matchMedia('(min-width: 768px)').addEventListener('change', () => {
  state.menuOpen = false;
  renderMenu();
});
themeButton.addEventListener('click', () => {
  state.theme = state.theme === 'light' ? 'dark' : 'light';
  renderTheme();
  try { localStorage.setItem('portfolio-theme', state.theme); } catch {
    // 저장이 차단된 환경에서도 현재 페이지의 테마 변경은 유지한다.
  }
});
document.querySelectorAll('a[href^="#"]').forEach((link) => {
  link.addEventListener('click', (event) => {
    const target = document.querySelector(link.getAttribute('href'));
    if (!target) return;
    event.preventDefault();
    state.menuOpen = false;
    renderMenu();
    scrollToSection(target);
  });
});
const updateScrollState = () => {
  state.scrolled = window.scrollY >= HEADER_SCROLL_THRESHOLD;
  state.showTopButton = window.scrollY >= TOP_BUTTON_THRESHOLD;
  renderScroll();
};
window.addEventListener('scroll', updateScrollState, { passive: true });
topButton.addEventListener('click', () => scrollToSection(document.querySelector('#hero')));
retryButton.addEventListener('click', loadProjects);

fields.forEach((field) => {
  form.elements.namedItem(field).addEventListener('input', () => {
    state.formErrors[field] = validateField(field);
    state.formSuccess = '';
    renderForm();
  });
});
form.addEventListener('submit', (event) => {
  event.preventDefault();
  state.formSuccess = '';
  fields.forEach((field) => {
    state.formErrors[field] = validateField(field);
  });
  const invalidField = fields.find((field) => state.formErrors[field]);
  if (!invalidField) {
    state.formSuccess = '입력 확인이 완료되었습니다. 메시지는 실제 전송되지 않았습니다.';
  }
  renderForm();
  if (invalidField) form.elements.namedItem(invalidField).focus();
});

try {
  const savedTheme = localStorage.getItem('portfolio-theme');
  if (savedTheme === 'dark' || savedTheme === 'light') state.theme = savedTheme;
} catch {
  state.theme = 'light';
}
renderTheme();
renderMenu();
renderForm();
updateScrollState();
document.querySelector('#year').textContent = new Date().getFullYear();

if ('IntersectionObserver' in window && !reducedMotion.matches) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(({ isIntersecting, target }) => {
      if (isIntersecting) {
        target.classList.add('is-visible');
        observer.unobserve(target);
      }
    });
  }, { threshold: REVEAL_THRESHOLD });
  // 긴 섹션 대신 작은 콘텐츠 단위를 관찰해 모바일에서도 20% 도달을 보장한다.
  document.querySelectorAll('.reveal').forEach((section) => {
    Array.from(section.children).forEach((element) => {
      if (element.matches('.about-layout, .skills-grid, .contact-layout')) {
        Array.from(element.children).forEach((child) => {
          child.classList.add('reveal', 'will-reveal');
          observer.observe(child);
        });
      } else if (!element.matches('#projects-grid, [hidden], noscript')) {
        element.classList.add('reveal', 'will-reveal');
        observer.observe(element);
      }
    });
  });
}
loadProjects();
