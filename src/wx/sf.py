destroy_sf_def= {
  "Comment": "A description of my state machine",
  "StartAt": "destroy cluster",
  "States": {
    "destroy cluster": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "OutputPath": "$.Payload",
      "Parameters": {
        "Payload.$": "$",
        "FunctionName": "arn:aws:lambda:us-east-2:880755836258:function:WX-clusterNestedStackclus-lambdafuncdestroy811B2A7-3cxqzYGHhxQz:$LATEST"
      },
      "Retry": [
        {
          "ErrorEquals": [
            "Lambda.ServiceException",
            "Lambda.AWSLambdaException",
            "Lambda.SdkClientException",
            "Lambda.TooManyRequestsException"
          ],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2
        }
      ],
      "Next": "Whether cluster could be deleted"
    },
    "Whether cluster could be deleted": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.cluster.clusterStatus",
          "StringEquals": "DELETE_IN_PROGRESS",
          "Next": "Wait for cluster deleting"
        }
      ],
      "Default": "Fail"
    },
    "Wait for cluster deleting": {
      "Type": "Wait",
      "Seconds": 60,
      "Next": "Monitor deleting status"
    },
    "Monitor deleting status": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "Payload.$": "$",
        "FunctionName": "arn:aws:lambda:us-east-2:880755836258:function:WX-clusterNestedStackclus-lambdafuncdestroy811B2A7-3cxqzYGHhxQz:$LATEST"
      },
      "Retry": [
        {
          "ErrorEquals": [
            "Lambda.ServiceException",
            "Lambda.AWSLambdaException",
            "Lambda.SdkClientException",
            "Lambda.TooManyRequestsException"
          ],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2
        }
      ],
      "Next": "Whether Success Deleted",
      "OutputPath": "$.Payload"
    },
    "Whether Success Deleted": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.cluster.clusterStatus",
          "StringEquals": "DELETE_COMPLETE",
          "Next": "Success"
        },
        {
          "Variable": "$.cluster.clusterStatus",
          "StringEquals": "DELETE_IN_PROGRESS",
          "Next": "Wait for cluster deleting"
        }
      ],
      "Default": "Fail"
    },
    "Fail": {
      "Type": "Fail"
    },
    "Success": {
      "Type": "Succeed"
    }
  }
}

create_sf_def= {
  "Comment": "A description of my state machine",
  "StartAt": "Create cluster",
  "States": {
    "Create cluster": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "OutputPath": "$.Payload",
      "Parameters": {
        "Payload.$": "$",
        "FunctionName": "arn:aws:lambda:us-east-2:880755836258:function:WX-clusterNestedStackclus-lambdafuncdestroy811B2A7-3cxqzYGHhxQz:$LATEST"
      },
      "Retry": [
        {
          "ErrorEquals": [
            "Lambda.ServiceException",
            "Lambda.AWSLambdaException",
            "Lambda.SdkClientException",
            "Lambda.TooManyRequestsException"
          ],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2
        }
      ],
      "Next": "Whether cluster could be created"
    },
    "Whether cluster could be created": {
      "Type": "Choice",
      "Choices": [
        {
          "Not": {
            "Variable": "$.clusterStatus",
            "StringEquals": "CREATE_IN_PROGRESS"
          },
          "Next": "Pass"
        }
      ],
      "Default": "Wait for cluster creating"
    },
    "Pass": {
      "Type": "Pass",
      "End": true
    },
    "Wait for cluster creating": {
      "Type": "Wait",
      "Next": "Monitor  creating status",
      "Seconds": 10
    },
    "Monitor  creating status": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "Payload.$": "$",
        "FunctionName": "arn:aws:lambda:us-east-2:880755836258:function:WX-clusterNestedStackclus-lambdafuncdestroy811B2A7-3cxqzYGHhxQz"
      },
      "Retry": [
        {
          "ErrorEquals": [
            "Lambda.ServiceException",
            "Lambda.AWSLambdaException",
            "Lambda.SdkClientException",
            "Lambda.TooManyRequestsException"
          ],
          "IntervalSeconds": 2,
          "MaxAttempts": 6,
          "BackoffRate": 2
        }
      ],
      "Next": "Whether Success Created",
      "OutputPath": "$.Payload"
    },
    "Whether Success Created": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.clusterStatus",
          "StringEquals": "CREATE_IN_PROGRESS",
          "Next": "Wait for cluster creating"
        }
      ],
      "Default": "Pass"
    }
  }
}

main_sf_def = {
  "Comment": "A description of my state machine",
  "StartAt": "Choice",
  "States": {
    "Choice": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.num_of_cluster",
          "NumericEquals": 1,
          "Next": "Create single OD Cluster"
        }
      ],
      "Default": "Parallel"
    },
    "Create single OD Cluster": {
      "Type": "Task",
      "Resource": "arn:aws:states:::states:startExecution.sync:2",
      "Parameters": {
        "StateMachineArn": "arn:aws:states:us-east-2:880755836258:stateMachine:ClusterCreate",
        "Input": {
          "action": "create",
          "type": "od",
          "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id"
        }
      },
      "OutputPath": "$.Output",
      "Next": "Choice (1)"
    },
    "Choice (1)": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.clusterStatus",
          "StringEquals": "CREATE_COMPLETE",
          "Next": "Publish completed message (1)"
        }
      ],
      "Default": "Publish Fail to create cluster message (1)"
    },
    "Publish Fail to create cluster message (1)": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-2:880755836258:WRF",
        "Message": {
          "message": "Clusters failed to be created complete, will start to destroy the cf",
          "detail information": {
            "OD cluster": {
              "cluster name": "$[0].clusterName"
            },
            "Spot cluster": {
              "cluster name": "$[1].clusterName"
            }
          }
        }
      },
      "ResultPath": null,
      "Next": "Destroy single Cluster"
    },
    "Publish completed message (1)": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-2:880755836258:WRF",
        "Message": {
          "message": "Clusters have been created successfully, will start to run forecast jobs",
          "detail information": {
            "OD cluster": {
              "cluster name": "$[0].clusterName",
              "head node": "$[0].headNode"
            },
            "Spot cluster": {
              "cluster name": "$[1].clusterName",
              "head node": "$[1].headNode"
            }
          }
        }
      },
      "ResultPath": null,
      "Next": "Pass (1)"
    },
    "Pass (1)": {
      "Type": "Pass",
      "Next": "Destroy single Cluster"
    },
    "Destroy single Cluster": {
      "Type": "Task",
      "Resource": "arn:aws:states:::states:startExecution.sync:2",
      "Parameters": {
        "StateMachineArn": "arn:aws:states:us-east-2:880755836258:stateMachine:ClusterDestroy",
        "Input": {
          "action": "destroy",
          "clusterName.$": "$.clusterName",
          "region.$": "$.region",
          "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id"
        }
      },
      "Next": "Choice (2)"
    },
    "Choice (2)": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.Output.cluster.clusterStatus",
          "StringEquals": "DELETE_COMPLETE",
          "Next": "Destroy failed notification (1)"
        }
      ],
      "Default": "Destroy complete notification (1)"
    },
    "Destroy complete notification (1)": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-2:880755836258:WRF",
        "Message": {
          "message": "Clusters has been deleted"
        }
      },
      "Next": "Success",
      "ResultPath": null
    },
    "Destroy failed notification (1)": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-2:880755836258:WRF",
        "Message": {
          "message": "Clusters failed to be deleted"
        }
      },
      "Next": "Fail",
      "ResultPath": null
    },
    "Parallel": {
      "Type": "Parallel",
      "Next": "Whether Success Created",
      "Branches": [
        {
          "StartAt": "Create OD Cluster",
          "States": {
            "Create OD Cluster": {
              "Type": "Task",
              "Resource": "arn:aws:states:::states:startExecution.sync:2",
              "Parameters": {
                "StateMachineArn": "arn:aws:states:us-east-2:880755836258:stateMachine:ClusterCreate",
                "Input": {
                  "action": "create",
                  "type": "od",
                  "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id"
                }
              },
              "OutputPath": "$.Output",
              "End": true
            }
          }
        },
        {
          "StartAt": "Create Spot Cluster",
          "States": {
            "Create Spot Cluster": {
              "Type": "Task",
              "Resource": "arn:aws:states:::states:startExecution.sync:2",
              "Parameters": {
                "StateMachineArn": "arn:aws:states:us-east-2:880755836258:stateMachine:ClusterCreate",
                "Input": {
                  "action": "create",
                  "type": "spot",
                  "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id"
                }
              },
              "End": true,
              "OutputPath": "$.Output"
            }
          }
        }
      ]
    },
    "Publish Fail to create cluster message": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-2:880755836258:WRF",
        "Message": {
          "message": "Clusters failed to be created complete, will start to destroy the cf",
          "detail information": {
            "OD cluster": {
              "cluster name": "$[0].clusterName"
            },
            "Spot cluster": {
              "cluster name": "$[1].clusterName"
            }
          }
        }
      },
      "Next": "Map",
      "ResultPath": null
    },
    "Whether Success Created": {
      "Type": "Choice",
      "Choices": [
        {
          "And": [
            {
              "Variable": "$[0].clusterStatus",
              "StringEquals": "CREATE_COMPLETE"
            },
            {
              "Variable": "$[1].clusterStatus",
              "StringEquals": "CREATE_COMPLETE"
            }
          ],
          "Next": "Publish completed message"
        }
      ],
      "Default": "Publish Fail to create cluster message"
    },
    "Publish completed message": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-2:880755836258:WRF",
        "Message": {
          "message": "Clusters have been created successfully, will start to run forecast jobs",
          "detail information": {
            "OD cluster": {
              "cluster name": "$[0].clusterName",
              "head node": "$[0].headNode"
            },
            "Spot cluster": {
              "cluster name": "$[1].clusterName",
              "head node": "$[1].headNode"
            }
          }
        }
      },
      "Next": "Pass",
      "ResultPath": null
    },
    "Pass": {
      "Type": "Pass",
      "Next": "Map"
    },
    "Map": {
      "Type": "Map",
      "ItemProcessor": {
        "ProcessorConfig": {
          "Mode": "DISTRIBUTED",
          "ExecutionType": "STANDARD"
        },
        "StartAt": "Destroy Cluster",
        "States": {
          "Destroy Cluster": {
            "Type": "Task",
            "Resource": "arn:aws:states:::states:startExecution.sync:2",
            "Parameters": {
              "StateMachineArn": "arn:aws:states:us-east-2:880755836258:stateMachine:ClusterDestroy",
              "Input": {
                "action": "destroy",
                "clusterName.$": "$.clusterName",
                "region.$": "$.region",
                "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id"
              }
            },
            "End": true
          }
        }
      },
      "Next": "Whether Success Deleted",
      "Label": "Map",
      "MaxConcurrency": 1000
    },
    "Whether Success Deleted": {
      "Type": "Choice",
      "Choices": [
        {
          "And": [
            {
              "Variable": "$[0].Output.cluster.clusterStatus",
              "StringEquals": "DELETE_COMPLETE"
            },
            {
              "Variable": "$[1].Output.cluster.clusterStatus",
              "StringEquals": "DELETE_COMPLETE"
            }
          ],
          "Next": "Destroy complete notification"
        }
      ],
      "Default": "Destroy failed notification"
    },
    "Destroy failed notification": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-2:880755836258:WRF",
        "Message": {
          "message": "Clusters failed to be deleted"
        }
      },
      "Next": "Fail",
      "ResultPath": null
    },
    "Destroy complete notification": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {
        "TopicArn": "arn:aws:sns:us-east-2:880755836258:WRF",
        "Message": {
          "message": "Clusters has been deleted"
        }
      },
      "Next": "Success",
      "ResultPath": null
    },
    "Fail": {
      "Type": "Fail"
    },
    "Success": {
      "Type": "Succeed"
    }
  }
}
