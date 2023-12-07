import React , { useState, useEffect } from "react";
import Map from "react-map-gl/maplibre";
import { Source, Layer,NavigationControl } from "react-map-gl/maplibre";
import '@aws-amplify/ui-react-geo/styles.css';
import "maplibre-gl/dist/maplibre-gl.css";

import config from "../../aws-export";

const mapApiKey = config.geo.amazon_location_service.maps.apikey.toString();
const region = config.aws_project_region.toString();
const mapName = config.geo.amazon_location_service.maps.default.toString();

interface MapProps {
    center:number[],
    size:number[]
}

const DomainMap = ({center,size}:MapProps) => {
    
    const [domainCenter,setDomainCenter] = useState<number[]>([]);
    const [domainSize,setDomainSize] = useState<number[]>([]);
    const [geoData,setGeoData] = useState<any>({});
    const [mapdata,setMapdata] = useState<any>({});
   /**
   * Compute the lon/lat point a given distance from another point
   *
   * @param pt1 Initial lon/lat point
   * @param dist Distances in kilometers [dx, dy] dx:+=north/-=south, dy:+=east/-=west
   * @return Distance in meters between the two points
   * @private
   */
    const haversineInverse=(pt1:number[], dist:number[]) => {
        const lon1: number = pt1[0];
        const lat1: number = pt1[1];
        const dx: number = dist[0];
        const dy: number = dist[1];
        const lat2: number = lat1 + (dy / 111120);
        const lon2: number = lon1 + (dx / (111120 * Math.abs(Math.cos(lat2 * Math.PI/180))));
        console.log(lon2,lat2);
        return [lon2, lat2];
    };

    const computeBox = (center:number[], size:number[]) => {        
        const refLat: number = center[0];
        const refLon: number = center[1];
        const dx: number = size[0];
        const dy: number = size[1];
        const nw: number[] = haversineInverse([refLon, refLat], [-dx / 2, -dy / 2]);
        const se: number[] = haversineInverse([refLon, refLat], [dx / 2, dy / 2]);
        const ne: number[] = [se[0],nw[1]];
        const sw: number[] = [nw[0],se[1]];
        console.log(nw,ne,se,sw);
        return [nw,ne,se,sw,nw];
    };

    const initialViewState = {
      latitude: center[0],
      longitude: center[1],
      zoom: 4
    };

    
    useEffect(()=>{
        console.log('domain center:',center);
        console.log('domain size:',size);

        
        if (center.length===0 || size.length===0) return;
        
        setDomainCenter(center);
        setDomainSize(size);
        setGeoData ({
          "type": "FeatureCollection",
          "features": [
            {
              "type": "Feature",
              "properties": {},
              "geometry": {
                "type": "Polygon",
                "coordinates": [computeBox(center,size)]
              }
            }
          ]
        });
        setMapdata({
          latitude: center[0],
          longitude: center[1],
          zoom: 15,
        });

    },[]);

    return (
      <Map
      // See https://visgl.github.io/react-map-gl/docs/api-reference/map
      initialViewState={initialViewState}
      style={{  width: "100%" }}
      mapStyle={`https://maps.geo.${region}.amazonaws.com/maps/v0/maps/${mapName}/style-descriptor?key=${mapApiKey}`}
    >
      {/* See https://visgl.github.io/react-map-gl/docs/api-reference/navigation-control */}
      <NavigationControl position="bottom-right" showZoom showCompass={false} />
  
      {/* Display the city of Vancouver as a polygon overlay */}
          <Source type="geojson" data={geoData}>
          {/* Create a map layer that displays the boundary and styles it
          See https://visgl.github.io/react-map-gl/docs/api-reference/layer */}
              <Layer type="fill" paint={{ "fill-color": "steelblue", "fill-opacity": 0.3 }} />
          </Source>
    </Map>
    );
};

export default DomainMap;