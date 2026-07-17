import React from "react";
import { Composition } from "remotion";
import { Hero } from "./Hero";

export const Root: React.FC = () => (
  <Composition
    id="hero"
    component={Hero}
    durationInFrames={480}
    fps={24}
    width={1200}
    height={500}
  />
);
