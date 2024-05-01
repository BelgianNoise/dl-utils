import React from "react";

const SVGCross = (props: {
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
        <path stroke={props.color ?? '#FFFFFF'} d="M19 5L4.99998 19M5.00001 5L19 19" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"></path>
      </g>
    </svg>
  );
};

export default SVGCross;
