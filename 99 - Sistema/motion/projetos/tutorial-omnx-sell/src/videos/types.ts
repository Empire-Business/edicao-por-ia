export type Focus = {x: number; y: number; w: number; h: number};

export type Scene =
  | {
      kind: 'title';
      durationInFrames: number;
      title: string;
      subtitle: string;
      kicker?: string;
    }
  | {
      kind: 'step';
      durationInFrames: number;
      step: number;
      image: string;
      title: string;
      caption: string;
      focus?: Focus;
      zoom?: number;
    }
  | {
      kind: 'note';
      durationInFrames: number;
      title: string;
      bullets: string[];
    };

export const S = (sec: number) => Math.round(sec * 30);

export const totalOf = (scenes: Scene[]) =>
  scenes.reduce((acc, s) => acc + s.durationInFrames, 0);

export const stepsOf = (scenes: Scene[]) =>
  scenes.reduce(
    (max, s) => (s.kind === 'step' && s.step > max ? s.step : max),
    0,
  );
