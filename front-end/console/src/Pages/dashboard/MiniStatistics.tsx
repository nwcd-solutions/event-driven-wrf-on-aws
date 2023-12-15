import React from "react";
import { Card,Loader } from "@aws-amplify/ui-react";

interface MiniStatisticProps {
  title: string;
  amount: string;
  icon?: JSX.Element;
  loading: boolean;
}

const MiniStatistics = (props: MiniStatisticProps) => {
  return (
    <Card height="100%" borderRadius="15px" className="bg-gradient-red">
      <div className="card-content">
        <div className="card-title"> {props.title} </div>
        {props.loading?
          <div className="card-statistics-amount"><Loader></Loader></div>
        :
          <div className="card-statistics-amount">{props.amount}</div>
        }
        <div className="card-statistics-icon">{props.icon}</div>
      </div>
    </Card>
  );
};

export default MiniStatistics;
