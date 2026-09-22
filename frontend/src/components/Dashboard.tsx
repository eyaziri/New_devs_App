import React, { useEffect, useState } from "react";
import { RevenueSummary } from "./RevenueSummary";
import { SecureAPI } from "../lib/secureApi";

interface Property {
  id: string;
  name: string;
  timezone: string;
}

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const Dashboard: React.FC = () => {
  const [properties, setProperties] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState('');
  const [loadingProperties, setLoadingProperties] = useState(true);
  // Sample reservation data currently only covers March 2024.
  const [month, setMonth] = useState(3);
  const [year, setYear] = useState(2024);

  useEffect(() => {
    const fetchProperties = async () => {
      setLoadingProperties(true);
      try {
        const response = await SecureAPI.getDashboardProperties();
        const fetched: Property[] = response?.properties || [];
        setProperties(fetched);
        if (fetched.length > 0) {
          setSelectedProperty(fetched[0].id);
        }
      } catch (err) {
        console.error('Failed to load properties', err);
      } finally {
        setLoadingProperties(false);
      }
    };

    fetchProperties();
  }, []);

  return (
    <div className="p-4 lg:p-6 min-h-full">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 text-gray-900">Property Management Dashboard</h1>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 lg:p-6">
          <div className="mb-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
              <div>
                <h2 className="text-lg lg:text-xl font-medium text-gray-900 mb-2">Revenue Overview</h2>
                <p className="text-sm lg:text-base text-gray-600">
                  Monthly performance insights for your properties
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-4">
                {/* Month/Year Selector */}
                <div className="flex flex-col sm:items-end">
                  <label className="text-xs font-medium text-gray-700 mb-1">Period</label>
                  <div className="flex gap-2">
                    <select
                      value={month}
                      onChange={(e) => setMonth(Number(e.target.value))}
                      className="block px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                    >
                      {MONTHS.map((name, index) => (
                        <option key={name} value={index + 1}>{name}</option>
                      ))}
                    </select>
                    <select
                      value={year}
                      onChange={(e) => setYear(Number(e.target.value))}
                      className="block px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                    >
                      {[2024, 2025, 2026].map((y) => (
                        <option key={y} value={y}>{y}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Property Selector */}
                <div className="flex flex-col sm:items-end">
                  <label className="text-xs font-medium text-gray-700 mb-1">Select Property</label>
                  <select
                    value={selectedProperty}
                    onChange={(e) => setSelectedProperty(e.target.value)}
                    disabled={loadingProperties || properties.length === 0}
                    className="block w-full sm:w-auto min-w-[200px] px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
                  >
                    {properties.length === 0 && (
                      <option value="">{loadingProperties ? 'Loading...' : 'No properties'}</option>
                    )}
                    {properties.map((property) => (
                      <option key={property.id} value={property.id}>
                        {property.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {selectedProperty && (
              <RevenueSummary propertyId={selectedProperty} month={month} year={year} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
