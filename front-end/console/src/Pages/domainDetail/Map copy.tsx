// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import React,{ useEffect, useState } from "react";
import Map from "react-map-gl/maplibre";
import { withIdentityPoolId } from "@aws/amazon-location-utilities-auth-helper";
import { Source, Layer,NavigationControl } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";





const DomainMap = () => {
    const [auth,setAuth] = useState<any>()
    const [geodata,setGeodata] = useState<any>(
        {
            "type": "FeatureCollection",
            "features": [
              {
                "type": "Feature",
                "properties": {},
                "geometry": {
                  "type": "Polygon",
                  "coordinates": [
                    [
                      [-123.22377204895018, 49.277898709435036],
                       [-123.20300102233887, 49.2583385255126],
                       [-123.19716453552246, 49.24612523123567],
                      [-123.19707870483398, 49.23514189153837],
                       [-123.15630912780762, 49.21078491050371],
                      [-123.15321922302246, 49.20823360010472],
                      [-123.22377204895018, 49.277898709435036]
                    ]
                  ]
                }
              }
            ]
          }
    );
    const identityPoolId = 'us-east-1:c5bec6aa-8ae9-4b8b-82bb-7fbbda3d1fd5';
    const region = 'us-east-1';
    const mapName = 'react-map-with-geojson-example';

    useEffect(() => { 
        async function getAuth() {
            const authHelper = await withIdentityPoolId(identityPoolId);
            setAuth(authHelper.getMapAuthenticationOptions);
            console.log(auth);
        }
        getAuth();
    },[]);
 
    return(
        <Map
            // See https://visgl.github.io/react-map-gl/docs/api-reference/map
            initialViewState={{
                latitude: 49.2819,
                longitude: -123.1187,
                zoom: 11,
            }}
            style={{ height: "100vh", width: "100vw" }}
            mapStyle={`https://maps.geo.${region}.amazonaws.com/maps/v0/maps/${mapName}/style-descriptor`}
            {...auth}
        >
            {/* See https://visgl.github.io/react-map-gl/docs/api-reference/navigation-control */}
            <NavigationControl position="bottom-right" showZoom showCompass={false} />
            <Source type="geojson" data={geodata}>
                {/* Create a map layer that displays the boundary and styles it
                See https://visgl.github.io/react-map-gl/docs/api-reference/layer */}
                <Layer type="fill" paint={{ "fill-color": "steelblue", "fill-opacity": 0.3 }} />
            </Source>
        </Map>
    );
};

export default DomainMap;