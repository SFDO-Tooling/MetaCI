export let settings: {
  setAssetsPath: (path: string) => void;
  getAssetsPath: () => string;
  setAppElement: (el: string | Element) => void;
  getAppElement: () => string | Element | undefined;
};

export default settings;
