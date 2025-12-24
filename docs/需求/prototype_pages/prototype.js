document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.wizard').forEach(wizard => {
    const steps = Array.from(wizard.querySelectorAll('.wizard-step'));
    const contentContainer = wizard.nextElementSibling;

    if (!contentContainer) {
      return;
    }

    const sections = Array.from(contentContainer.querySelectorAll('[data-step]'));
    const stepMap = new Map();

    steps.forEach(step => {
      const stepId = step.getAttribute('data-step');
      const section = sections.find(sec => sec.getAttribute('data-step') === stepId);
      if (!section) {
        return;
      }
      stepMap.set(step, section);

      step.addEventListener('click', () => {
        setActiveStep(step);
      });

      const navPrev = section.querySelector('[data-nav="prev"]');
      const navNext = section.querySelector('[data-nav="next"]');

      if (navPrev) {
        navPrev.addEventListener('click', () => {
          const currentIndex = steps.indexOf(step);
          if (currentIndex > 0) {
            setActiveStep(steps[currentIndex - 1]);
          }
        });
      }

      if (navNext) {
        navNext.addEventListener('click', () => {
          const currentIndex = steps.indexOf(step);
          if (currentIndex < steps.length - 1) {
            setActiveStep(steps[currentIndex + 1]);
          }
        });
      }
    });

    const setActiveStep = targetStep => {
      if (!targetStep || !stepMap.has(targetStep)) {
        return;
      }

      const activeIndex = steps.indexOf(targetStep);

      steps.forEach((step, index) => {
        const section = stepMap.get(step);
        const isActive = step === targetStep;
        step.classList.toggle('active', isActive);
        step.classList.toggle('completed', index < activeIndex);
        if (section) {
          section.classList.toggle('active-section', isActive);
          const navPrev = section.querySelector('[data-nav="prev"]');
          const navNext = section.querySelector('[data-nav="next"]');
          if (navPrev) {
            navPrev.disabled = activeIndex === 0;
          }
          if (navNext) {
            navNext.disabled = activeIndex === steps.length - 1;
            navNext.textContent = activeIndex === steps.length - 1 ? '完成' : '下一步';
          }
        }
      });
    };

    const initialStep = wizard.querySelector('.wizard-step.active') || steps[0];
    setActiveStep(initialStep);
  });

  // 横向 tab 菜单
  document.querySelectorAll('.tab-menu').forEach(menu => {
    const buttons = Array.from(menu.querySelectorAll('button[data-tab-target]'));
    const container = menu.nextElementSibling;
    if (!container) {
      return;
    }

    const panels = Array.from(container.querySelectorAll('[data-tab]'));

    const setActiveTab = target => {
      buttons.forEach(btn => {
        const isActive = btn === target;
        btn.classList.toggle('active', isActive);
      });

      panels.forEach(panel => {
        const shouldShow = panel.getAttribute('data-tab') === target.getAttribute('data-tab-target');
        panel.classList.toggle('active', shouldShow);
      });
    };

    buttons.forEach(btn => {
      btn.addEventListener('click', () => setActiveTab(btn));
    });

    setActiveTab(menu.querySelector('button[data-tab-target].active') || buttons[0]);
  });
});
