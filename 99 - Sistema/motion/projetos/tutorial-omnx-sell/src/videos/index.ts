import type {Brand} from '../theme';
import type {Scene} from './types';

import {omnxBrand, omnxScenes} from './omnx';

export const videos: {id: string; brand: Brand; scenes: Scene[]}[] = [
  {id: 'OmnxAnalise', brand: omnxBrand, scenes: omnxScenes},
];
