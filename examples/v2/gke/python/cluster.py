# Copyright 2016 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Create configuration to deploy GKE cluster."""


def GenerateConfig(context):
  """Generate YAML resource configuration."""

  name_prefix = context.env['deployment'] + '-' + context.env['name']
  cluster_name = name_prefix
  type_name = name_prefix + '-type'

  resources = [
      {
          'name': cluster_name,
          'type': 'container.v1.cluster',
          'properties': {
              'zone': context.properties['zone'],
              'cluster': {
                  'name': cluster_name,
                  'initialNodeCount': context.properties['numNodes'],
                  'nodeConfig': {
                      'oauthScopes': [
                          'https://www.googleapis.com/auth/' + s
                          for s in [
                              'compute', 'devstorage.read_only',
                              'logging.write', 'monitoring'
                          ]
                      ]
                  },
                  'masterAuth': {
                      'username': context.properties['username'],
                      'password': context.properties['password']
                  }
              }
          }
      },
      {
          'name': type_name,
          'type': 'deploymentmanager.alpha.typeProvider',
          'properties': {
              'options': {
                  'validationOptions': {
                      # Kubernetes API accepts ints, in fields they annotate
                      # with string. This validation will show as warning rather
                      # than failure for Deployment Manager.
                      # https://github.com/kubernetes/kubernetes/issues/2971
                      'schemaValidation': 'IGNORE_WITH_WARNINGS'
                  },
                  # According to kubernetes spec, the path parameter 'name'
                  # should be the value inside the metadata field
                  # https://github.com/kubernetes/community/blob/master/contributors/devel/api-conventions.md
                  # This mapping specifies that
                  'inputMappings': [{
                      'fieldName': 'name',
                      'location': 'PATH',
                      'methodMatch': '^(GET|DELETE|PUT)$',
                      'value': '$.ifNull($.resource.properties.metadata.name, '
                               '$.resource.name)'
                  }, {
                      'fieldName': 'metadata.name',
                      'location': 'BODY',
                      'methodMatch': '^(PUT|POST)$',
                      'value': '$.ifNull($.resource.properties.metadata.name, '
                               '$.resource.name)'
                  }]
              },
              'descriptorUrl':
                  ''.join([
                      'https://$(ref.', cluster_name,
                      '.endpoint)/swaggerapi/api/v1'
                  ]),
              'credential': {
                  'basicAuth': {
                      'user':
                          '$(ref.' + cluster_name + '.masterAuth.username)',
                      'password':
                          ''.join(
                              ['$(ref.', cluster_name, '.masterAuth.password)'])
                  }
              }
          }
      }
  ]

  outputs = [{'name': 'clusterType', 'value': type_name}]

  return {'resources': resources, 'outputs': outputs}
