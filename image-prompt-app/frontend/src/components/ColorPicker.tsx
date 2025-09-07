import React, { useState } from 'react';

const ColorPicker: React.FC = () => {
  const [color, setColor] = useState('#ffffff');

  const handleColorChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setColor(e.target.value);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(color);
  };

  return (
    <div className="color-picker-container">
      <h4>Color Palette</h4>
      <div className="color-picker-input-wrapper">
        <input
          type="color"
          value={color}
          onChange={handleColorChange}
          className="color-input"
        />
        <div className="color-display" style={{ backgroundColor: color }}></div>
      </div>
      <div className="hex-code-wrapper">
        <input type="text" readOnly value={color} />
        <button onClick={copyToClipboard}>Copy</button>
      </div>
    </div>
  );
};

export default ColorPicker;
