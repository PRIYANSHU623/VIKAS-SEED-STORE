export default function Loader() {
  return (
    <div className="flex justify-center items-center h-[60vh]">

      <div className="flex flex-col items-center gap-4">

        <div
          className="
          w-12
          h-12
          border-4
          border-green-500
          border-t-transparent
          rounded-full
          animate-spin
          "
        />

        <p className="text-gray-600">
          Loading...
        </p>

      </div>
    </div>
  );
}