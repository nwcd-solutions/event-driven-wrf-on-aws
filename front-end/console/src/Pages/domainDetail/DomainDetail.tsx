import React,{ useEffect, useState } from "react";
import { View, Heading,Grid,TextField,Tabs,Button,Flex,Loader } from "@aws-amplify/ui-react";
import { useParams, useNavigate } from "react-router-dom";
import { Domain } from "../settings/Domain"
import { get,put } from 'aws-amplify/api';
import  Namelist  from "./Namelist";
import DomainMap from "./Map";
import Location from "./Location";

interface DomainDetailProps {
  getToken:()=>void;
}

const DomainDetail = ({getToken}:DomainDetailProps) => {
  const navigate = useNavigate();
  let {id}=useParams() ;
  const [loading, setLoading] = useState(false);
  const [title,setTitle] = useState('');
  const [error, setError] = useState<string | undefined>(undefined);
  const [domain,setDomain] = useState<Domain>();
  const [wpsNamelist,setWpsNameList] = useState<any>({});
  const [wrfNamelist,setWrfNameList] = useState<any>({});
  const [latlonPoint,setLatlonPoint] = useState<string>('');
  const [domainSize,setDomainSize] = useState<number[]>([]);
  const [domainCenter,setDomainCenter] = useState<number[]>([]);

  const parseNamelist = (text: string): object =>{
    const namelist: any = {'sections': []};

    /* split the string into an array of strings by section */
    const sections: Array<string> = text.split('&');

    /* throw away the first string if it is empty */
    while (sections[0] === '')
      sections.splice(0, 1);

    /* create a section object for each section */
    for (let section of sections)
    {
      const lines: Array<string> = section.split('\n');

      while (lines[0] === '')
        lines.splice(0, 1);

      const sectionName: string = lines.splice(0, 1)[0];
      const values: any = {'names': []};
      namelist['sections'].push(sectionName);
      for (let line of lines)
      {
        /* check for a section terminator */
        if (line.trim().startsWith('/'))
          break;

        /* build the sections name/value pairs */
        const tokens: Array<string> = line.split('=');
        while (tokens[0] === '')
          tokens.splice(0, 1);

        /* if this is not a name=value pair, it is a continuation of the previous value */
        if (tokens.length < 2)
        {
          const lastName: string = values.names[values.names.length - 1];
          values[lastName] += line;
          continue;
        }

        /* parse the name/value pair and add them to the dictionary */
        const name: string = tokens[0].trim();
        const value: string = tokens[1].trim();
        values['names'].push(name);
        values[name] = value;
      }
      namelist[sectionName] = values;
    }

    return namelist;
  }

  const unparseNamelist = (namelist: any): string =>
  {
    /* initialize an empty string to append */
    let text: string = '';

    /* add each section of the name list */
    for (let section of namelist.sections)
    {
      /* skip empty sections */
      if (section === '')
        continue;

      /* add the section header */
      text += '&' + section + '\n';

      /* add all of the name/value pairs in the section */
      for (let name of namelist[section].names)
        text += '  ' + name + ' = ' + namelist[section][name] + '\n';
      text += '/\n\n';
    }

    return text;
  };

  async function UpdateDomain() {
    setLoading(true);    

    try {        
      const { body } = await put({
        apiName: 'WrfAPIGateway',
        path: '/domain/',        
        options: {
          headers: {
            Authorization: await getToken()!,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
          },  
          body: {
            data:{
              model_config:JSON.stringify(domain)
            }            
          }               
        }
      }).response;   

      setError(''); 
    }
    catch (e) {
      if (e instanceof Error) {
        setError(e.message);
        console.log(e)
      }
    } finally {
      setLoading(false);
      navigate(-1);
    }
  }
  
  async function loadDomain(name:string) {
    setLoading(true);
    try {        
      const { body } = await get({
        apiName: 'WrfAPIGateway',
        path: '/domain/',
        options: {
          headers: {
            Authorization: await getToken()!,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
          },
          queryParams: {
            configuration_name: name
          }
        }
      }).response;        

      const domain:Domain=await body.json() as any;
      
      setLatlonPoint('[ Latitude: '+ String(domain?.domain_center?.latitude) +' , Longitude: '+ String(domain?.domain_center?.longitude) +' ]');

      setError('');
      setDomain(domain);
      if ((domain != null) && ('wps_namelist' in domain)){
        setWpsNameList(parseNamelist(domain.wps_namelist));
       
      };
      if ((domain != null) && ('wrf_namelist' in domain)){
        setWrfNameList(parseNamelist(domain.wrf_namelist));
     
      }
      if ((domain != null) && ('domain_size' in domain)){
        setDomainSize(domain.domain_size);

      }
         
      let a:number[]=[];
      if ((domain != null) && ('domain_center' in domain)){
          let lat=domain.domain_center?.latitude;
          let lon=domain.domain_center?.longitude;    
          if (lat && lon){
              a.push(lat);
              a.push(lon);
              setDomainCenter(a);
          }
      }
    }
    catch (e) {
      if (e instanceof Error) {
        setError(e.message);
        console.log(e)
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLocationUpdate =(location:any)=>{
    if (domain !=null){
      setDomain({...domain,location:location});
     
    }
  
  };
  const handleNamelistUpdate = (namelist:string,type:string) => {
    if (domain !=null){
      if (type=='wps'){
        setDomain({...domain,wps_namelist:namelist});
   
      }else if (type=='wrf'){
        setDomain({...domain,wrf_namelist:namelist});
 
      }else if(type=='wrf_bk'){
        setDomain({...domain,wrf_bk_namelist:namelist});
    
      }
   
    }   
  };

  const handleCheck =  () => {

    if (domain !=null){
      //setDomain({...domain});
    } 
  };

  const handleCancel = () => {
    navigate(-1);
  };

  const handleUpdate = () =>{
    if (domain !=null){
      UpdateDomain();
    }  
  }
 
  const handleChange = (e: { target: { name: any; value: any; }; }) => {
    const { name, value } = e.target;
    if (domain !=null){
      setDomain({ ...domain, [name]: value });
    }
  };  

  useEffect(() => { 
    //if id is not null
    if(id){
      loadDomain(id);
      let h='Domain' + JSON.stringify(id) + 'Detail Information';
      
      setTitle(h);     
    }
    else{
      setDomain(undefined);
      setTitle("Create New Domain")
    }   
  },[]);

  return (
    <>
     
      <View padding="1rem">
          <Heading color="#333" level={5}>{title}</Heading>
      </View>
      { loading ? <Loader  size="large" variation="linear"></Loader> :
      <Grid
          columnGap="0.5rem"
          rowGap="0.5rem"
          templateColumns="1fr 1fr 1fr"
          templateRows="1fr 1fr 0.1fr"
          
      >
          <View
              backgroundColor="var(--amplify-colors-white)"
              borderRadius="6px"       
              padding="2rem"
              minHeight="50vh"
              columnStart="1"
              columnEnd="2"
              
          >
              <TextField label="Name (Read only)" name="name" variation="quiet" isReadOnly={true} defaultValue={domain?.name} width={'70%'}/>
              <br></br>
              <TextField label="Description" name="description" variation="quiet" defaultValue={domain?.description} width={'70%'} onChange={handleChange} />
              <br></br>
              <TextField label="Cores" variation="quiet" defaultValue={domain?.cores} width={'70%'}/>
              <br></br>
              <TextField label="Domain Center (Read only)" variation="quiet" isReadOnly={true} defaultValue={latlonPoint} width={'70%'}/ >
              <br></br>
              <TextField label="Domain Size (Read only)" variation="quiet" isReadOnly={true} defaultValue={ JSON.stringify(domain?.domain_size)} width={'70%'}/>
          </View>
          <View
              backgroundColor="var(--amplify-colors-white)"
              borderRadius="6px"   
              padding="1rem"
              minHeight="50vh"
              columnStart="2"
              columnEnd="-1"
          ><DomainMap center={domainCenter} size={domainSize} /></View>
          <View
              backgroundColor="var(--amplify-colors-white)"
              borderRadius="6px"
              padding="2rem"
              columnStart="1"
              columnEnd="-1"
          >
              <Tabs
                  defaultValue={'Tab 1'}
                  items={[
                  { 
                      label: 'WPS Namelist', 
                      value: 'Tab 1', 
                      content:  domain?.wps_namelist ?
                                (<Namelist namelist={ domain?.wps_namelist} type={'wps'} onUpdate = {handleNamelistUpdate}></Namelist>) :null
                                
                  },
                  { 
                      label: 'Primary WRF Namelist', 
                      value: 'Tab 2', 
                      content: domain?.wrf_namelist ?(<Namelist namelist={ domain?.wrf_namelist} type={'wrf'} onUpdate = {handleNamelistUpdate}></Namelist>) :null 
                  },
                  { 
                      label: 'Second WRF Namelist', 
                      value: 'Tab 3', 
                      content: domain?.wrf_bk_namelist ?(<Namelist namelist={ domain?.wrf_bk_namelist} type={'wrf_bk'} onUpdate = {handleNamelistUpdate}></Namelist>) :null 
                  },
                  { 
                    label: 'Location', 
                    value: 'Tab 4', 
                    content: domain?.location ?
                             (<Location location={ domain?.location}  onUpdate = {handleLocationUpdate}></Location>) :
                             (<Location location={ []}  onUpdate = {handleLocationUpdate}></Location>)
                },
                  ]}
              />
          </View>
          <View
              backgroundColor="var(--amplify-colors-white)"
              borderRadius="6px"   
              padding="2rem"
              columnStart="1"
              columnEnd="-1"
          >
              <Flex justifyContent="flex-end">
                  <Button
                      width={'200px'}    
                      onClick={handleCancel}      
                  >Cancel</Button>
                  <Button
                      width={'200px'}      
                      onClick={handleCheck}    
                  >Duplicate</Button>
                  <Button
                      variation="primary" 
                      width={'200px'}    
                      onClick={handleUpdate}
                  >Update</Button>
              </Flex>
          </View>
      </Grid>
       }
    </>
  );
};

export default DomainDetail;
