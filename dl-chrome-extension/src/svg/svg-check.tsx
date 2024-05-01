import React from "react";

const SVGCheck = (props: {
  color?: string,
  width?: string,
  height?: string,
}) => {
  return (
    <svg
      width={props.width ?? '25px'}
      height={props.height ?? '25px'}
      viewBox="0 0 24 24"
      fill="none"
    >
      <g id="SVGRepo_iconCarrier">
        <path stroke={props.color ?? '#FFFFFF'} d="M4 12.6111L8.92308 17.5L20 6.5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"></path>
      </g>
    </svg>
  );
};

export default SVGCheck;
