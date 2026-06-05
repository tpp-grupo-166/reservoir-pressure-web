interface StepIndicatorProps {
  currentStep: number; // 0, 1 o 2
  totalSteps?: number;
}

export function StepIndicator({ currentStep, totalSteps = 3 }: StepIndicatorProps) {
  return (
    <div className="stepper">
      {Array.from({ length: totalSteps }, (_, i) => {
        const done    = i < currentStep;
        const active  = i === currentStep;

        const circleClass = [
          'stepper__circle',
          active ? 'stepper__circle--active' : '',
          done   ? 'stepper__circle--done'   : '',
        ].filter(Boolean).join(' ');

        const labelClass = [
          'stepper__label',
          active ? 'stepper__label--active' : '',
        ].filter(Boolean).join(' ');

        return (
          <div key={i} className="stepper__step">
            <div className={circleClass}>
              {done
                ? <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>check</span>
                : i + 1
              }
            </div>
            <span className={labelClass}>Paso {i + 1}</span>
          </div>
        );
      })}
    </div>
  );
}
