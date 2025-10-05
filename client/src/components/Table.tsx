import React from 'react';

interface TableColumn<T> {
  header: string;
  accessor: keyof T | string;
  className?: string;
  cell?: (row: T) => React.ReactNode;
}

interface TableProps<T> {
  columns: TableColumn<T>[];
  data: T[];
  keyField?: keyof T;
  emptyMessage?: string;
  className?: string;
  rowClassName?: string | ((row: T, index: number) => string);
}

const Table = <T extends { id?: string | number }>({
  columns,
  data,
  keyField = 'id' as keyof T,
  emptyMessage = 'No data available',
  className = '',
  rowClassName = '',
}: TableProps<T>) => {
  if (data.length === 0) {
    return (
      <div className="flex justify-center items-center p-8 text-gray-500">
        {emptyMessage}
      </div>
    );
  }

  const getRowClassName = (row: T, index: number): string => {
    const baseClasses = 'hover:bg-gray-50';
    const customClass = typeof rowClassName === 'function' 
      ? rowClassName(row, index) 
      : rowClassName;
    
    return `${baseClasses} ${customClass}`.trim();
  };

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full">
        <thead>
          <tr className="text-left text-gray-500 text-sm bg-gray-50">
            {columns.map((col) => (
              <th
                key={String(col.accessor)}
                className={`${col.className || ''} px-4 py-3 font-medium`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {data.map((row, rowIndex) => (
            <tr 
              key={String(row[keyField] || rowIndex)}
              className={getRowClassName(row, rowIndex)}
            >
              {columns.map((col) => (
                <td 
                  key={String(col.accessor)}
                  className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap"
                >
                  {col.cell ? col.cell(row) : (row[col.accessor as keyof T] as React.ReactNode) || '-'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Table;
