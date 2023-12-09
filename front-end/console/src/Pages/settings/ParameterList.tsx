import React , { useState ,useEffect} from "react";
import {
  Table,
  TableCell,
  TableBody,
  TableHead,
  TableRow,
  Button,
  Flex
} from "@aws-amplify/ui-react";

import { MOCK_PARAMETERS } from "./mock";
import { Parameter } from "./Parameter"

interface ParaTableProps {
  parameters:Parameter[];
  onEdit:(parameter:Parameter)=>void;
}

const ParaTable = ({parameters,onEdit}:ParaTableProps) => {

  return (
    <>
      <Table caption="" highlightOnHover={false}>
        <TableHead>
          <TableRow>
          
            <TableCell as="th">Parameter</TableCell>
            <TableCell as="th">Description</TableCell>
            <TableCell as="th">Value</TableCell>
            <TableCell as="th"></TableCell>
            
          </TableRow>
        </TableHead>

        <TableBody>
          {parameters?.map((item) => {
            return (
              <TableRow key={item.name}>
             
                <TableCell>{item.name}</TableCell>
                <TableCell>{item.description}</TableCell>
                <TableCell>{item.value}</TableCell>
                <TableCell>
                  <Flex justifyContent="flex-end">
                    <Button onClick={() => { onEdit(item)} }>Edit</Button>
                  </Flex>
                  
                </TableCell>
             
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </>
  );
};

export default ParaTable;
