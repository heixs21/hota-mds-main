import { createContext, useContext } from "react";

/** 当前切片是否为轮播选中页；用于保持各页挂载并暂停后台轮询 */
export const ScreenCarouselPageContext = createContext({ isActive: true });

export function useScreenCarouselPageActive() {
  return useContext(ScreenCarouselPageContext).isActive;
}
