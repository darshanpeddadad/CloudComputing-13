import React, { useState } from "react";
import { Map, Marker } from "pigeon-maps";

const LocationPicker = ({ lat, lng, onChange }) => {
  const [position, setPosition] = useState([lat || 50.1109, lng || 8.6821]);

  const handleClick = ({ latLng }) => {
    const [lat, lng] = latLng;
    setPosition([lat, lng]);
    onChange({ lat, lng });
  };

  return (
    <div className="w-full h-64 rounded-md overflow-hidden border">
      <Map
        height={260}
        defaultCenter={position}
        center={position}
        zoom={13}
        onClick={handleClick}
      >
        <Marker
          width={40}
          anchor={position}
          onDragEnd={({ latLng }) => {
            const [lat, lng] = latLng;
            setPosition([lat, lng]);
            onChange({ lat, lng });
          }}
        />
      </Map>
    </div>
  );
};

export default LocationPicker;
