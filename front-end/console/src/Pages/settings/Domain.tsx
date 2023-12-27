export interface LatLonPoint
{
  latitude: number;
  longitude: number;
}

export class Domain {
    name: string = '';
    description: string = '';
    cores: number = 0;
    model_name: string ='wrf';  /* This should always be WRF until we support other models */
    wrf_namelist: string = '';
    wrf_bk_namelist: string = '';
    wps_namelist: string =  '';
    location:any = [];
    domain_center?: LatLonPoint;
    domain_size: number[]=[0,0];    
    s3_key_wrf_namelist?:string = '';
    s3_key_wrf_bk_namelist?:string = '';
    s3_key_wps_namelist?:string = '';
    s3_key_geo_em?:string = '';

    constructor(initializer?: any) {
      if (!initializer) return;
      if (initializer.name) this.name = initializer.name;
      if (initializer.description) this.description = initializer.description;
      if (initializer.cores) this.cores = initializer.cores;
      if (initializer.model_name) this.model_name = initializer.model_name;
      if (initializer.wrf_namelist) this.wrf_namelist = initializer.wrf_namelist;
      if (initializer.wps_namelist) this.wps_namelist = initializer.wps_namelist;
      if (initializer.domain_center) this.domain_center = initializer.domain_center;
      if (initializer.domain_size) this.domain_size = initializer.domain_size;
      if (initializer.s3_key_wrf_namelist) this.s3_key_wrf_namelist = initializer.s3_key_wrf_namelist;
      if (initializer.s3_key_wps_namelist) this.s3_key_wps_namelist = initializer.s3_key_wps_namelist;
      if (initializer.s3_key_geo_em) this.s3_key_geo_em = initializer.s3_key_geo_em;
      if (initializer.s3_key_wrf_bk_namelist) this.s3_key_wrf_bk_namelist = initializer.s3_key_wrf_bk_namelist;
      if (initializer.wrf_bk_namelist) this.wrf_bk_namelist = initializer.wrf_bk_namelist;
      if (initializer.location) this.location = initializer.location;
    
          
    }
  }
