import React ,{ useState, useEffect } from "react";
import {
  Table,
  TableCell,
  TableBody,
  TableHead,
  TableRow,
  Button,
  Flex,
  View
} from "@aws-amplify/ui-react";
import { Domain } from "./Domain"
import { useNavigate } from "react-router-dom";
import config from "../../aws-export";
const bucket=config.aws_user_files_s3_bucket;

interface DomainTableProps {
  domains:Domain[];
  onDelete:(name:string)=>void;
}

const DomainTable = ({domains, onDelete}:DomainTableProps) => {

  const navigate = useNavigate();

  const handleEdit = (name:string) => {
    navigate(`/domain/${name}`);  
  };
  const handleCreate = () => {
    navigate("/domain");
  };

  return (
    <>
      <View >
        <br></br>
          <Button variation="primary" onClick={ ()=> { handleCreate()}}>Created New Domain</Button>
          <br></br>
          <br></br>
      </View>
      { domains.length === 0 ? 
        <View>
          <br></br>
          <h4>No Domain Found</h4>
          <br></br>
        </View>
        :
      <Table caption="" highlightOnHover={false}>
        <TableHead>
          <TableRow>
            <TableCell as="th">Domain Name</TableCell>
            <TableCell as="th">Description</TableCell>
            <TableCell as="th">Cores</TableCell>
            <TableCell as="th">Domain Center</TableCell>
            <TableCell as="th">Domain Size</TableCell>
            <TableCell as="th">Files Location</TableCell>
            <TableCell as="th"></TableCell>
          </TableRow>
        </TableHead>

        <TableBody>

          {domains?.map((item) => {
            return (
              <TableRow key={item.name}>
                <TableCell>{item.name}</TableCell>
                <TableCell>{item.description}</TableCell>
                <TableCell>{item.cores}</TableCell>
                <TableCell> [ lat: {item.domain_center?.latitude} , lon: {item.domain_center?.longitude} ]  </TableCell>
                <TableCell> [ {item.domain_size[0]},{item.domain_size[1]} ]   </TableCell>
                <TableCell> s3://{bucket}/{item.s3_key_wrf_namelist?.substring(0,item.s3_key_wrf_namelist.lastIndexOf('/'))}/  </TableCell>
        
                <TableCell>
                  <Flex justifyContent="flex-end">
                    <Button  onClick={ ()=> { handleEdit(item.name) } }>Edit</Button>
                    <Button variation="primary" colorTheme="error" onClick={ ()=> { onDelete(item.name) } }>Delete</Button>
                  </Flex>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      }
    </>
  );
};

export default DomainTable;
